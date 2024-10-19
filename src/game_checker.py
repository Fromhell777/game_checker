import os

import asyncio
import aiohttp
import requests
from lxml import etree

# Get the HTML from a url
def get_html_data(url):
  html = requests.get(url).text

  return html


async def fetch_url(session, url):
  async with session.get(url, timeout = 60) as response:
    print(f"Collecting games from: {url}")
    return await response.text()

async def fetch_all_urls(session, urls, loop):
  results = await asyncio.gather(*[fetch_url(session, url) for url in urls],
                                 return_exceptions = True)
  return results

def get_htmls(urls):
  if len(urls) > 1:
    loop = asyncio.get_event_loop()
    connector = aiohttp.TCPConnector(limit = 100)
    with aiohttp.ClientSession(loop = loop, connector = connector) as session:
      htmls = loop.run_until_complete(fetch_all_urls(session, urls, loop))
    raw_result = dict(zip(urls, htmls))
  else:
    raw_result = {url[0]: requests.get(urls[0]).text}

  return raw_result






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

def get_game_list(url):

  print(f"Collecting games from: {url}")

  games = set()

  html_tree = etree.HTML(get_html_data(url))
  for _, elem in etree.iterwalk(html_tree, tag = "a", ):
    if ("class" in elem.attrib) and \
       elem.attrib["class"] == "product-title px_list_page_product_click list_page_product_tracking_target":
      games.add(elem.text.replace("\n", ""))

  return games

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
    print("#######################\n")
    print("### New games found ###\n")
    print("#######################\n")
    print('\n'.join(sorted(new_games)))

  # Find games that were removed
  removed_games = set()
  for game in prev_game_list:
    if game not in game_list:
      removed_games.add(game)

  if removed_games:
    print("\n###########################\n")
    print("### Removed games found ###\n")
    print("###########################\n")
    print('\n'.join(sorted(removed_games)))

  # Update the previous game list
  with open(prev_game_list_file, 'w') as f:
    f.write('\n'.join(sorted(game_list)))



base_url = "https://www.bol.com/be/nl/l/games-voor-de-ps5/51867/?page={0}"
log_dir = "./logs"

max_page_number = get_max_page_number((base_url.format(1)))
#max_page_number = 2

urls = [base_url.format(i) for i in range(1, max_page_number + 1)]
result_dict = get_htmls(urls)

all_games = set()

for i in range(1, max_page_number + 1):
  url = base_url.format(i)
  all_games = all_games.union(get_game_list(url))

check_games(all_games, log_dir)

