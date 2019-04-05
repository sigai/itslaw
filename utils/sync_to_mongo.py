"""
sync to mongodb first, then merge redis judgement id data
"""

import json

from redis import Redis
import pymongo


client = pymongo.MongoClient()
db = client.atersoft
coll = db.wusong_judgements_000

r = Redis()

def upload():
    while True:
        item = r.spop("itslaw:judgement")
        if not item:
            break
        try:
            doc = str(item, encoding="utf-8")
            doc = json.loads(doc)
            r.sadd("itslaw:jid", doc["id"])
            doc["_id"] = doc["id"]
            doc.pop("id")

            res = coll.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
            if res.acknowledged:
                print(f"[+] {res.upserted_id}")
        except Exception as e:
            r.sadd("itslaw:judgement", item)
            print(e)
        

def merge_id():
    res = r.sdiffstore("itslaw:id", "itslaw:id", "itslaw:jid")
    print(res)
    res = r.sunionstore("itslaw:crawled", "itslaw:crawled", "itslaw:jid")
    print(res)

def dump():
    while True:
        item = r.spop("itslaw:judgement")
        if not item:
            break
        try:
            doc = json.loads(str(item, encoding="utf-8"))
            with open("docs.txt", mode="a", encoding="utf-8") as f:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        except Exception as e:
            r.sadd("itslaw:judgement", item)
            print(e)
            break

def load():
    with open("docs.txt", mode="r", encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line.strip())
            doc["_id"] = doc["id"]
            doc.pop("id")
            try:
                res = coll.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
                if res.acknowledged:
                    print(f"[+] {res.upserted_id}")
            except Exception as e:
                print(e)
            

if __name__ == "__main__":
    load()