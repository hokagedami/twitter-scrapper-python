import time
from pathlib import Path
import asyncio
import json

import pandas as pd

import twitter
import concurrent.futures

NUM_RETRIES = 3
NUM_THREADS = 2

output = Path(__file__).parent / "results"
output.mkdir(exist_ok=True)

data = Path(__file__).parent / "data"


async def run():
    twitter.BASE_CONFIG["debug"] = True

    print("running Twitter scrape and saving results to ./results directory")
    start = time.time()
    chunk = pd.read_csv(data.joinpath("usernames.csv"), chunksize=1000)
    end = time.time()
    print("Read csv with chunks: ", (end - start), "sec")
    pd_df = pd.concat(chunk)
    usernames = pd_df['username'].astype(str).tolist()
    for username in usernames:
        await twitter.write_profile_to_json(username)

    # url = "https://twitter.com/codekage_"
    # profile = await twitter.scrape_profile(url)
    # output.joinpath("profile.json").write_text(json.dumps(profile, indent=2, ensure_ascii=False))


if __name__ == "__main__":

    asyncio.run(run())
