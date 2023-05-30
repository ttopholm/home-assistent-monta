from fastapi import FastAPI
import requests
from os import environ
import uuid

app = FastAPI()

monta_url = "https://api.monta.app/api/v1/charge_points/map"
monta_charge_point_url = "https://api.monta.app/api/v1/charge_points"

api_headers = {
    "Authorization": environ.get("monta-auth-token"),
    "Meta": "web;production;1.0.0;browser;edge%20Win32",
    "Operator": environ.get("monta-operator", "monta"),
    "Timezone": environ.get("monta-timezone", "CEST"),
    "UUID": str(uuid.uuid4()),
    "Accept-Language": environ.get('language', 'da')
}

query_parameters = {
    "top": environ.get("bbox-top"),
    "bottom": environ.get("bbox-bottom"),
    "left": environ.get("bbox-left"),
    "right": environ.get("bbox-right"),
    "zoom": environ.get("zoom", 15),   
    "center_lat": environ.get("center-lat"),
    "center_lng": environ.get("center-lng"),
    "busy_all": environ.get("monta-busy", 0),
    "passive": environ.get("monta-passive", 0),
    "min_kw": environ.get("monta-min-kw", 0)
}


@app.get("/")
def read_root():
    try:
        r = requests.get(monta_url, params=query_parameters, headers=api_headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    result_json = r.json()
    results = []
    for cp in result_json.get('list'):
        match cp.get('document'):
            case "charge_point":

                results.append({
                    "name": cp.get('name'),
                    "address": f'{cp.get("address1")}, {cp.get("address2")}',
                    "price": float(''.join(c for c in cp.get('price_label') if (c.isdigit() or c =='.'))),
                    "price_label": cp.get('price_label'),
                    "available": cp.get('available')
                })
            case "charge_point_group":
                charge_query_parameters = {
                    "charge_point_group_id": cp.get('id')
                }
                try:
                    r = requests.get(monta_charge_point_url, params=charge_query_parameters, headers=api_headers)
                    r.raise_for_status()
                except requests.exceptions.HTTPError as err:
                    raise SystemExit(err)
                charge_points = r.json()
                for cp in charge_points.get('data'):
                    results.append({
                        "name": cp.get('name'),
                        "address": f'{cp.get("address1")}, {cp.get("address2")}',
                        "price": float(''.join(c for c in cp.get('pricings').get('public_label') if (c.isdigit() or c =='.'))),
                        "price_label": cp.get('pricings').get('public_label'),
                        "available": cp.get('available')
                    })

    sorted_list = sorted(results, key=lambda x: x.get('price'))
    return sorted_list[0]