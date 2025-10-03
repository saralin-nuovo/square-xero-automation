# utils/http.py
import requests
from flask import jsonify

def safe_get(url, headers=None, params=None, timeout=30):
    """Wrapper for GET with basic error handling."""
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        if resp.status_code != 200:
            return None, jsonify({"error": resp.status_code, "body": resp.text}), 400
        return resp.json(), None, 200
    except requests.RequestException as e:
        return None, jsonify({"error": "request_failed", "message": str(e)}), 500


def safe_post(url, headers=None, json=None, data=None, timeout=30):
    """Wrapper for POST with basic error handling."""
    try:
        resp = requests.post(url, headers=headers, json=json, data=data, timeout=timeout)
        if resp.status_code not in (200, 201):
            return None, jsonify({"error": resp.status_code, "body": resp.text}), 400
        return resp.json(), None, resp.status_code
    except requests.RequestException as e:
        return None, jsonify({"error": "request_failed", "message": str(e)}), 500
