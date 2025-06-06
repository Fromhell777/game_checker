import os
import argparse
import time
import datetime
import subprocess

import asyncio
import aiohttp
import requests
from lxml import etree

import smtplib, ssl
import getpass

# Get the HTML from a url
def get_html_data(url):
  html = requests.get(url).text

  return html

def get_max_page_number(url):

  print(f"Collecting max page number from: {url}")

  html_tree = etree.HTML(get_html_data(url))

  max_page_number = 1

  for _, elem in etree.iterwalk(html_tree, tag = "a", ):
    if ("class" in elem.attrib) and \
       elem.attrib["class"] == "js_pagination_item":
      max_page_number = max(max_page_number, int(elem.text))

  print(f"Max page number: {max_page_number}")

  return max_page_number

async def get_games_async(session, url):
  print(f"Collecting games from: {url}")

  async with session.get(url, timeout = 60) as response:
    games = set()

    html = await response.text()

    html_tree = etree.HTML(html)
    for _, elem in etree.iterwalk(html_tree, tag = "a"):
      if ("class" in elem.attrib) and \
         elem.attrib["class"] == "product-title px_list_page_product_click list_page_product_tracking_target":
        games.add(elem.text.replace("\n", ""))

    return games

async def get_all_games(urls):
  print("Extracting game lists")

  async with aiohttp.ClientSession() as session:
    tasks = []
    for url in urls:
      tasks.append(asyncio.create_task(get_games_async(session, url)))

    games = await asyncio.gather(*tasks)

  return set().union(*games)

def check_games(game_list, log_dir):

  print(f"\nChecking game lists")

  os.makedirs(log_dir, exist_ok = True)

  # Write the game list if no list exists yet
  prev_game_list_file = f"{log_dir}/prev_game_list.txt"
  if not os.path.isfile(prev_game_list_file):
    with open(prev_game_list_file, 'w') as f:
      f.write('\n'.join(sorted(game_list)))

    return

  # Read the previous game list
  with open(prev_game_list_file, 'r') as f:
    prev_game_list = set(f.read().splitlines())

  # Read the full game list that we have seen before
  seen_game_list = set()
  seen_game_list_file = f"{log_dir}/seen_game_list.txt"
  if os.path.isfile(seen_game_list_file):
    with open(seen_game_list_file, 'r') as f:
      seen_game_list = set(f.read().splitlines())

  # Find games that are new
  new_games = set()
  for game in game_list:
    if game not in prev_game_list and \
       game not in seen_game_list:
      new_games.add(game)

  if new_games:
    print("\n#######################")
    print("### New games found ###")
    print("#######################")
    print('\n'.join(sorted(new_games)))

  # Find games that were removed
  removed_games = set()
  for game in prev_game_list:
    if game not in game_list:
      removed_games.add(game)

  if removed_games:
    print("\n###########################")
    print("### Removed games found ###")
    print("###########################")
    print('\n'.join(sorted(removed_games)))

  if (not new_games) and (not removed_games):
    print("\n##################")
    print("### No changes ###")
    print("##################")

  # Update the previous game list
  with open(prev_game_list_file, 'w') as f:
    f.write('\n'.join(sorted(game_list)))

  # Update the full game list that we have seen before
  with open(seen_game_list_file, 'w') as f:
    f.write('\n'.join(sorted(seen_game_list.union(game_list))))

  return new_games, removed_games

def send_email(sender_email, receiver_email, password, new_games,
               removed_games):

  print(f"\nSending mail")

  port = 465  # For SSL
  smtp_server = "smtp.gmail.com"
  message = "Subject: Game list update\n\n"

  if new_games:
    message += "\n#######################\n"
    message += "### New games found ###\n"
    message += "#######################\n\n"
    message += '\n'.join(sorted(new_games))
    message += "\n"

  if removed_games:
    message += "\n###########################\n"
    message += "### Removed games found ###\n"
    message += "###########################\n\n"
    message += '\n'.join(sorted(removed_games))
    message += "\n"

  context = ssl.create_default_context()
  with smtplib.SMTP_SSL(smtp_server, port, context = context) as server:
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)


# Setup program interface
parser = argparse.ArgumentParser(prog        = "game_checker" ,
                                 description = "Check game availability")
parser.add_argument("-e", "--with_email",
                    action = "store_true",
                    help   = "Send email notifications")
parser.add_argument("-a", "--notify_all",
                    action = "store_true",
                    help   = "Send email for new and removed games. Only " + \
                             "valid with the --with_email option")
parser.add_argument("-l", "--loop",
                    action = "store_true",
                    help   = "Loop the checking script")
parser.add_argument("-t", "--test_email",
                    action = "store_true",
                    help   = "Test sending email notifications")
args = parser.parse_args()

if args.notify_all and (not args.with_email):
  parser.error("--notify_all requires --with_email.")

# Get email info if needed
if args.with_email or args.test_email:
  sender_email   = input("Type the sender email and press enter: ")
  receiver_email = input("type the receiver email and press enter: ")
  password       = getpass.getpass(prompt = "Type your password and press enter: ")

# Check the games
#base_url = "https://www.bol.com/be/nl/l/games-voor-de-ps5/51867/?page={0}" # For all games
base_url = "https://www.bol.com/be/nl/l/games-voor-de-ps5-te-reserveren/51867/1285/?page={0}" # For pre-order games
log_dir = "./logs"

if args.test_email:
  send_email(sender_email   = sender_email,
             receiver_email = receiver_email,
             password       = password,
             new_games      = ["Test game"],
             removed_games  = [])

while True:
  print(f"Current time: {datetime.datetime.now()}")

  try:
    max_page_number = get_max_page_number((base_url.format(1)))

    urls = [base_url.format(i) for i in range(1, max_page_number + 1)]

    all_games = asyncio.run(get_all_games(urls))

    new_games, removed_games = check_games(all_games, log_dir)

    if args.with_email:
      if args.notify_all and (new_games or removed_games):
        send_email(sender_email   = sender_email,
                   receiver_email = receiver_email,
                   password       = password,
                   new_games      = new_games,
                   removed_games  = removed_games)
      elif (not args.notify_all) and new_games:
        send_email(sender_email   = sender_email,
                   receiver_email = receiver_email,
                   password       = password,
                   new_games      = new_games,
                   removed_games  = None)
  except Exception as error:
    print(f"\nAn exception occurred: {error}\n")

  if args.loop:
    print("\nWait some time before going to sleep\n")
    time.sleep(30)
    subprocess.call(f"sudo rtcwake --mode mem --seconds {60 * 60}", shell = True)
    print("\nWait some time after waking up\n")
    time.sleep(30)
  else:
    break
