#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from typing import Dict, List
from urllib.parse import urljoin, urlparse

import click
import requests
from requests.auth import HTTPBasicAuth
from ruamel.yaml import YAML, scalarstring

yaml = YAML()


@click.group()
def cli():
    pass


@cli.command()
@click.argument(
    "path",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, resolve_path=True
    ),
)
def download(path: str):
    """Download dashboards in YAML list at `PATH`. Minor special handling for
    `grafana.com/api` URLs.
    """
    download_dir = Path(path).parent
    entries = []
    with open(path) as f:
        entries = yaml.load(f)
    for entry in entries:
        url = entry["url"]
        data = requests.get(url, allow_redirects=True)

        # setup filename here - expectation is that each
        # (last_component_of_url_path, folder) will be unique
        filename = Path(urlparse(url).path).name
        if not filename.endswith(".json"):
            filename += ".json"

        # special handling for grafana API
        if url.startswith("https://grafana.com/api"):
            content = json.loads(data.content)
            # go through .links[] looking for download link
            url_path = (
                "/api"
                + next(
                    filter(lambda e: e["rel"] == "download", content["links"])
                )["href"]
            )
            url = urljoin(url, url_path)
            data = requests.get(url, allow_redirects=True)

        download_file = Path(download_dir, entry["folder"], filename)
        download_file.parent.mkdir(parents=True, exist_ok=True)
        with open(download_file, "wb") as download_fp:
            download_fp.write(data.content)


@cli.command()
@click.argument(
    "dashboard_dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True
    ),
)
def serialize_to_kustomize(dashboard_dir: str):
    """Given a dashboard directory, print out the corresponding configMap for
    the `deployment-patch-provisioning.yml`"""
    items: List[Dict[str, str]] = []
    config_map_generator_entries = []
    yaml.indent(mapping=2, sequence=2, offset=0)
    yaml.default_flow_style = False
    for f in Path(dashboard_dir).glob("**/*.json"):
        key = f.relative_to(dashboard_dir)
        path = f.relative_to(Path(dashboard_dir).parent)
        items.append(
            {
                "key": scalarstring.DoubleQuotedScalarString(str(key)),
                "path": scalarstring.DoubleQuotedScalarString(str(path)),
            }
        )

        config_map_generator_entries.append(
            scalarstring.DoubleQuotedScalarString(
                f.relative_to(Path(dashboard_dir).parent.parent)
            )
        )

    overlay_dir = Path(dashboard_dir).parent.parent.relative_to(
        Path(".").resolve()
    )
    print("---")
    print(f"# {overlay_dir / 'deployment-patch-provisioning.yml'}")
    yaml.dump(items, sys.stdout)
    print("---")
    print(f"# {overlay_dir / 'kustomization.yml'}")
    yaml.dump(config_map_generator_entries, sys.stdout)


@cli.command()
@click.argument(
    "dashboard_dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True
    ),
)
@click.option("--username", type=str)
@click.option("--password", type=str)
@click.option("--endpoint", type=str)
def upload(dashboard_dir: str, username: str, password: str, endpoint: str):
    """Uploads dashboards to grafana"""
    if username is None:
        username = "admin"
    if password is None:
        password = "admin"
    if endpoint is None:
        raise RuntimeError("Need --endpoint")
    endpoint = endpoint.rstrip("/")
    endpoint += "/api/dashboards/db"
    for dashboard_file in Path(dashboard_dir).glob("**/*.json"):
        print(dashboard_file)
        dashboard_data = json.loads(dashboard_file.read_text())
        # allows creation; if `id` is defined, it will refuse to create. The
        # uid should be sufficient.
        dashboard_data["id"] = None
        res = requests.post(
            url=endpoint,
            json={
                "dashboard": dashboard_data,
                "folderId": 0,
                "message": "uploading dasbhoard",
                "overwrite": True,
            },
            auth=HTTPBasicAuth(username=username, password=password),
        )
        if not res.ok:
            print(res.status_code, res.content)


if __name__ == "__main__":
    cli()
