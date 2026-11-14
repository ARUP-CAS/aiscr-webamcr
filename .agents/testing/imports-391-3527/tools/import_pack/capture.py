"""Resumable bounded direct GET evidence collection for complete large datasets."""

import re

from .common import digest, inside, read_json, save_json, write_new


def capture(reader, root, plan, limit=100, progress=None, evidence_root=None):
    evidence_root = (evidence_root or root).resolve()
    if not root.resolve().is_relative_to(evidence_root):
        raise ValueError("Capture folder must remain inside this run's evidence root")
    if not 1 <= limit <= 100000:
        raise ValueError("Explicit capture budget must be between 1 and 100000 GETs")
    urls = [item["url"] for item in plan["resources"]]
    if len(urls) != len(set(urls)):
        raise ValueError("Duplicate resource in capture plan")
    results, requested = [], 0
    for url in urls:
        if not re.fullmatch(
            r"https://fedora-test\.aiscr\.cz/rest/AMCR/record/[A-Za-z0-9-]+(?:/[A-Za-z0-9_:/.-]+)?", url
        ) or any(part in (".", "..") for part in url.split("/")):
            raise ValueError("Capture must target explicit test record resources")
        key = digest(url.encode())
        metadata = inside(root, "responses/" + key + ".json")
        body_path = inside(root, "responses/" + key + ".bin")
        if metadata.exists():
            response = read_json(metadata)
            if (
                response["url"] != url
                or not body_path.is_file()
                or (response.get("sha256") and digest(body_path.read_bytes()) != response["sha256"])
            ):
                raise ValueError("Retained response was changed")
        elif requested < limit:
            response = reader.get(url, "text/turtle" if url.endswith("/fcr:versions") else "*/*")
            write_new(body_path, response.pop("body"))
            response["body_path"] = body_path.relative_to(evidence_root).as_posix()
            save_json(metadata, response)
            requested += 1
            if progress and requested % 25 == 0:
                progress({"captured_this_call": requested, "retained": len(results) + 1, "planned": len(urls)})
        else:
            continue
        results.append(response)
        if response["status"] in (401, 403):
            break  # retain the control response; avoid repeating failed authentication
    index = {"resources": results, "planned": len(urls), "complete": len(results) == len(urls), "state": "captured"}
    from .common import json_bytes

    path = inside(root, "index-" + digest(json_bytes(index))[:16] + ".json")
    save_json(path, index)
    return {
        "index": str(path.resolve()),
        "new_requests": requested,
        "complete": index["complete"],
        "remaining": len(urls) - len(results),
    }
