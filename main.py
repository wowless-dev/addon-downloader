import requests
from operator import itemgetter
from google.cloud import storage

bucket = storage.Client().bucket("wowless.dev")

flavors = {
    "Mainline": 517,
    "TBC": 73246,
    "Vanilla": 67408,
}

session = requests.Session()
session.headers.update({"User-Agent": "wowless-dev/addon-downloader"})
session.hooks = {"response": lambda r, *args, **kwargs: r.raise_for_status()}


def download(cfid):
    print(f"finding downloads for cfid {cfid}")
    cfg = session.get(
        f"https://addons-ecs.forgesvc.net/api/v2/addon/{cfid}"
    ).json()
    lfmap = {
        f["id"]: f["downloadUrl"]
        for f in cfg["latestFiles"]
        if "-nolib" not in f["displayName"] and not f["isAlternate"]
    }
    gvlfs = list(
        filter(
            lambda f: f["projectFileId"] in lfmap,
            cfg["gameVersionLatestFiles"],
        )
    )
    gvlfs.sort(key=itemgetter("projectFileId"), reverse=True)
    gvlfs.sort(key=itemgetter("fileType"))
    for flavor_name, flavor_id in flavors.items():
        for gvlf in filter(
            lambda f: f["gameVersionTypeId"] == flavor_id, gvlfs
        ):
            url = lfmap[gvlf["projectFileId"]]
            print(f"{cfid} {flavor_name}: {url}")
            bucket.blob(f"addons/{cfid}-{flavor_name}.zip").upload_from_string(
                session.get(url).content, content_type="application/zip"
            )
            break


def handler(req):
    download(req.args["cfid"])
    return ""


if __name__ == "__main__":
    import sys

    download(sys.argv[1])
