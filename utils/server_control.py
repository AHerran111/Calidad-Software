import requests
import streamlit as st
import tomllib
import os

def load_token():
    try:
        return dict(st.secrets["do_token"])["token"]
    
    except Exception:
        secrets_path = os.path.dirname(__file__)+"/secrets.toml"

        with open(secrets_path, "rb") as f:
            config = tomllib.load(f)

        return config["do_token"]["token"]

DO_TOKEN = load_token()
print(DO_TOKEN)

DROPLETS = {
    "postgres_cliente": "570747060",
    "postgres_pac": "570800542",
    "api_pac": "570668624",
}

def droplet_action(droplet_id, action):
    url = f"https://api.digitalocean.com/v2/droplets/{droplet_id}/actions"

    headers = {
        "Authorization": f"Bearer {DO_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "type": action
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()


def start_infrastructure():
    for droplet_id in DROPLETS.values():
        droplet_action(droplet_id, "power_on")

def stop_infrastructure():
    for droplet_id in DROPLETS.values():
        droplet_action(droplet_id, "shutdown")