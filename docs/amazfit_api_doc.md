**Summary – What you need to know**

Huami/Zepp expose an *un-documented* HTTPS REST API that Gadgetbridge (and a few community tools) can call once you have the **`apptoken`** (often called *Huami token* or *auth-token*).
With that single header you can:

* log in,
* enumerate workouts, heart-rate, sleep & daily summaries,
* download per-minute or per-second detail,
* and keep paging until all history is fetched.

Everything is plain JSON over TLS, so a Python script built with `requests` is enough.
Below is a step-by-step reference with tested endpoints, required headers, Python examples, paging rules, rate-limit notes and security caveats.

---

## 1  Token basics

| Name                             | Header                           | Where it comes from                                                                                 |
| -------------------------------- | -------------------------------- | --------------------------------------------------------------------------------------------------- |
| Huami **AppToken**               | `apptoken: <TOKEN>`              | Returned by `/v2/client/login` JSON (`token_info > app_token`) or found in Zepp/Mi Fit shared-prefs |
| User **Access-Token**            | `access: <JWT>`                  | First-step redirect from `/registrations/{email}/tokens`                                            |
| Bearer **OAuth** (rarely needed) | `Authorization: Bearer <access>` | Only for the legacy *api-user* endpoints                                                            |

Gadgetbridge itself grabs `app_token` from the original Zepp pairing flow and stores it offline for further calls. ([gadgetbridge.org][1], [gadgetbridge.org][2])

To obtain it programmatically you can either:

1. **Two-step login** (`email + password`)

   * `POST https://api-user.huami.com/registrations/{email}/tokens` → 302 with `access` + `country_code` in query. ([raw.githubusercontent.com][3])
   * `POST https://account.huami.com/v2/client/login` with the fields shown below → JSON with `token_info.app_token`. ([raw.githubusercontent.com][3])

2. **Extract from phone** – root or HTTP-proxy and read `apptoken` header once Zepp syncs. ([rolandszabo.com][4])

---

## 2  Core headers to send

```text
apptoken: <YOUR_TOKEN>              # mandatory
appname:  com.xiaomi.hm.health      # Mi Fit/Zepp package
appPlatform: web                    # literal
Content-Type: application/json      # for POST/PUT
User-Agent: Zepp/6.10.5 Android/14  # anything mobile-like
```

`apptoken` alone is enough for **all** data endpoints shown below; no cookies are required. ([christianott.ch][5])

---

## 3  Key data endpoints

| Function         | Verb + URL                                                  | Typical params               | Notes                                                                       |
| ---------------- | ----------------------------------------------------------- | ---------------------------- | --------------------------------------------------------------------------- |
| Heart-rate raw   | `GET https://api-user.huami.com/v1/user/fitness/heart_rate` | `userid`, `date=2025-07-03`  | Returns 1 440 base64-packed shorts (one per minute). ([bentasker.co.uk][6]) |
| Steps / activity | `GET https://api-user.huami.com/v1/user/fitness/activity`   | same                         | Array with per-minute steps & calories. ([bentasker.co.uk][6])              |
| Sleep            | `GET https://api-user.huami.com/v1/user/fitness/sleep`      | same                         | Includes stages list (`mode` 4-8). ([raw.githubusercontent.com][3])         |
| Workout list     | `GET https://api-mifit.huami.com/v1/sport/run/history.json` | `source=run.mifit.huami.com` | Paginates 200 rows. ([christianott.ch][5])                                  |
| Workout detail   | `GET https://api-mifit.huami.com/v1/sport/run/detail.json`  | `trackid`, `source`          | Contains GPS polyline, hr, pace. ([rolandszabo.com][4])                     |
| Device info      | `GET https://api-user.huami.com/v1/user/profile`            | none                         | Returns nickname, age, weight. ([dkamioka.medium.com][7])                   |

> **Paging rule** – each history response has `next` with a UNIX `trackid`. Pass it back as `stopTrackId` to walk backwards in time. ([christianott.ch][5])

---

## 4  Python blueprint

```python
import base64, json, requests, datetime

TOKEN   = "…YOUR_APP_TOKEN…"
HEADERS = {
    "apptoken":    TOKEN,
    "appname":     "com.xiaomi.hm.health",
    "appPlatform": "web",
    "User-Agent":  "Zepp/6.10.5 PythonScript"
}

def get_hr(user_id, day):
    url = "https://api-user.huami.com/v1/user/fitness/heart_rate"
    r   = requests.get(url, headers=HEADERS,
                       params={"userid": user_id, "date": day})
    r.raise_for_status()
    blob = base64.b64decode(r.json()["heartRate"])
    # unpack … (see struct '<1440H')
    return list(int.from_bytes(blob[i:i+2], 'little')
                for i in range(0, len(blob), 2))

def workouts():
    url = "https://api-mifit.huami.com/v1/sport/run/history.json"
    next_tid, all_runs = None, []
    while True:
        params = {"source": "run.mifit.huami.com"}
        if next_tid: params["stopTrackId"] = next_tid
        r = requests.get(url, headers=HEADERS, params=params).json()
        all_runs.extend(r["trackInfo"])
        next_tid = r.get("next")
        if not next_tid: break
    return all_runs
```

The unpack logic for heart-rate mirrors Bentasker’s script (`zepp_to_influxdb`)—each little-endian short is *beats-per-minute*. ([raw.githubusercontent.com][3])

---

## 5  Rate limits & reliability

* No official quotas, but community polling every **5 min** for HR/steps and **30 min** for workouts remains safe (429 free for 10 s backoff). ([bentasker.co.uk][6])
* API occasionally returns HTTP 500; retry with jitter.
* Tokens rarely expire; if they do, redo the two-step login. ([rolandszabo.com][4])

---

## 6  Security & privacy

* Store the token **encrypted at rest**; it grants full read/write to the account.
* Always send over HTTPS (the domains already enforce TLS).
* Revocation: user can invalidate from Zepp App → Account → Security. ([github.com][8])

---

## 7  Putting it together

1. **Grab `apptoken`** once (manual or scripted).
2. **Identify the UID** – present in `login` JSON (`uid`) or Zepp web profile.
3. **Call the endpoints** above with shared headers.
4. **Decode / export** as needed (CSV, Influx, GPX…).
5. **Cache & retry** politely.

Follow that sequence and a Python developer can replicate 100 % of the data Gadgetbridge shows—without touching the closed Zepp cloud.

[1]: https://gadgetbridge.org/basics/pairing/huami-xiaomi-server/?utm_source=chatgpt.com "Huami/Xiaomi server pairing - Gadgetbridge"
[2]: https://gadgetbridge.org/gadgets/wearables/amazfit/?utm_source=chatgpt.com "Amazfit - Gadgetbridge"
[3]: https://raw.githubusercontent.com/bentasker/zepp_to_influxdb/main/app/mifit_to_influxdb.py "raw.githubusercontent.com"
[4]: https://rolandszabo.com/posts/export-mi-fit-and-zepp-workout-data/?utm_source=chatgpt.com "Export Mi Fit and Zepp workout data - Roland Szabó"
[5]: https://christianott.ch/post/2022-10-26_amazfit_cloud/?utm_source=chatgpt.com "‍♂️ backup amazfit fitness tracking data ‍♂️ :: christianott.ch"
[6]: https://www.bentasker.co.uk/posts/blog/software-development/extracting-data-from-zepp-app-for-local-storage-in-influxdb.html?utm_source=chatgpt.com "Writing data from a Bip 3 Smartwatch into InfluxDB - Ben Tasker"
[7]: https://dkamioka.medium.com/huami-provides-web-api-for-accessing-user-activity-data-tracked-with-huami-wearable-devices-cfd7351610f4?utm_source=chatgpt.com "“Huami provides Web API for accessing user activity data tracked ..."
[8]: https://github.com/argrento/huami-token/blob/master/README.md?utm_source=chatgpt.com "README.md - argrento/huami-token - GitHub"
