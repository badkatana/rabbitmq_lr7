import sys
import re
import requests
from bs4 import BeautifulSoup
import pika


def get_internal_links(url):
    internal_links = set()
    domain = re.match(r'https?://([^/]+)', url).group(0)

    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/'):
                href = domain + href
            elif not href.startswith('http'):
                href = f"{domain}/{href}"

            if domain in href:
                internal_links.add(href)
                title = link.get_text(strip=True)
                print(f"Found link: {title} - {href}")

    except Exception as e:
        print(f"Error fetching {url}: {e}")

    return internal_links


def main():
    if len(sys.argv) != 2:
        print("Usage: provide URL ")
        return

    url = sys.argv[1]
    rabbitmq_url = 'localhost'

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitmq_url))
    channel = connection.channel()
    channel.queue_declare(queue='links_queue')

    internal_links = get_internal_links(url)

    for link in internal_links:
        channel.basic_publish(
            exchange='', routing_key='links_queue', body=link)
        print(f"Published to queue: {link}")

    connection.close()


if __name__ == "__main__":
    main()
