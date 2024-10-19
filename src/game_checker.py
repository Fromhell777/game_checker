import os

import asyncio
import aiohttp
import requests
from lxml import etree

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

  print(f"\nChecking game lists\n")

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

  # Find games that are new
  new_games = set()
  for game in game_list:
    if game not in prev_game_list:
      new_games.add(game)

  if new_games:
    print("#######################")
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
    print("##################")
    print("### No changes ###")
    print("##################")

  # Update the previous game list
  with open(prev_game_list_file, 'w') as f:
    f.write('\n'.join(sorted(game_list)))



base_url = "https://www.bol.com/be/nl/l/games-voor-de-ps5/51867/?page={0}"
log_dir = "./logs"

max_page_number = get_max_page_number((base_url.format(1)))

urls = [base_url.format(i) for i in range(1, max_page_number + 1)]

all_games = asyncio.run(get_all_games(urls))

check_games(all_games, log_dir)
