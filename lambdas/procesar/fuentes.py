import json
import urllib.request
import urllib.parse

import boto3


ssm = boto3.client("ssm")


def obtener_memes():
    return obtener_memes_imgflip()


def obtener_memes_imgflip():
    url = "https://api.imgflip.com/get_memes"

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=10
    ) as response:
        data = json.loads(
            response.read().decode("utf-8")
        )

    memes = data.get(
        "data",
        {}
    ).get(
        "memes",
        []
    )

    return [
        {
            "name": meme["name"],
            "url": meme["url"],
            "source": "imgflip"
        }
        for meme in memes
    ]


def obtener_jamendo_client_id():
    response = ssm.get_parameter(
        Name="/funny-videos/jamendo-client-id",
        WithDecryption=True
    )

    return response["Parameter"]["Value"]


def obtener_musica(tags, velocidad):
    client_id = obtener_jamendo_client_id()

    def buscar(params):
        url = (
            "https://api.jamendo.com/v3.0/tracks/?"
            + urllib.parse.urlencode(params)
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        return data.get("results", [])

    # Intento 1:
    # tags + velocidad + instrumental
    params = {
        "client_id": client_id,
        "format": "json",
        "limit": 8,
        "include": "musicinfo",
        "vocalinstrumental": "instrumental",
        "speed": velocidad,
        "fuzzytags": " ".join(tags),
    }

    resultados = buscar(params)

    # Intento 2:
    # quitar velocidad
    if not resultados:
        print(
            "Jamendo: sin resultados con velocidad, "
            "reintentando solo con tags"
        )

        params.pop(
            "speed",
            None
        )

        resultados = buscar(params)

    # Intento 3:
    # usar solo el primer tag
    if not resultados and tags:
        print(
            "Jamendo: sin resultados con todos los tags, "
            "reintentando con un solo tag"
        )

        params["fuzzytags"] = tags[0]

        resultados = buscar(params)

    # Intento 4:
    # cualquier instrumental
    if not resultados:
        print(
            "Jamendo: usando fallback instrumental"
        )

        params.pop(
            "fuzzytags",
            None
        )

        resultados = buscar(params)

    return [
        {
            "name": track.get("name"),
            "artist_name": track.get("artist_name"),
            "duration": track.get("duration"),
            "audio": track.get("audio"),
            "shareurl": track.get("shareurl"),
            "license_ccurl": track.get(
                "license_ccurl",
                ""
            ),
        }
        for track in resultados
    ]