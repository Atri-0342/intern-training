import concurrent.futures
import urllib.request
import urllib.error
from collections import Counter

URL = "https://hrs-cottage-council-lafayette.trycloudflare.com/v1/debug/slow?seconds=10"

REQUEST_COUNT = 205
TIMEOUT = 45


def send_request(request_id: int):
    try:
        with urllib.request.urlopen(URL, timeout=TIMEOUT) as response:
            return request_id, response.status

    except urllib.error.HTTPError as error:
        return request_id, error.code

    except Exception as error:
        return request_id, type(error).__name__


def main():
    print(f"Sending {REQUEST_COUNT} concurrent requests...")
    print(f"URL: {URL}")
    print("Each request stays open for about 30 seconds.\n")

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=REQUEST_COUNT
    ) as executor:
        results = list(
            executor.map(
                send_request,
                range(1, REQUEST_COUNT + 1)
            )
        )

    counts = Counter(status for _, status in results)

    print("\n=== Result counts ===")
    for status, count in sorted(
        counts.items(),
        key=lambda item: str(item[0])
    ):
        print(f"{status}: {count}")

    successful = sum(1 for _, status in results if status == 200)
    rate_limited = sum(1 for _, status in results if status == 429)

    print("\n=== Summary ===")
    print(f"200 OK : {successful}")
    print(f"429    : {rate_limited}")


if __name__ == "__main__":
    main()