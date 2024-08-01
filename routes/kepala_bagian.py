from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from models import mongo
from datetime import datetime
from pymongo import MongoClient, DESCENDING

kepala_bagian_bp = Blueprint(
    "api/kepala_bagian", __name__, url_prefix="/api/kepala_bagian"
)

_client = MongoClient('mongodb://selvi:selvi@ac-ou90izj-shard-00-00.37a1b2k.mongodb.net:27017,ac-ou90izj-shard-00-01.37a1b2k.mongodb.net:27017,ac-ou90izj-shard-00-02.37a1b2k.mongodb.net:27017/?ssl=true&replicaSet=atlas-4a46gy-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0')
_db = _client['inventory_app'] # Ganti dengan nama database Anda
_items_collection = _db['items']

@kepala_bagian_bp.route("/ajukan", methods=["GET"])
def ajukan():
    # Retrieve all items that are verified
    verified_items = list(mongo.db.sub_bag.find({"is_verif": True}))
    for item in verified_items:
        item["_id"] = str(item["_id"])

    new_documents = []

    for sub_bag in verified_items:
        # Check if the document already exists in kepala_bagian
        existing_document = mongo.db.kepala_bagian.find_one({
            "id_sub_bag": sub_bag["_id"],
            "tanggal_pengusulan": sub_bag["tanggal_penerimaan"],
            "nama_barang": sub_bag["nama_barang"],
            "volume": sub_bag["volume"],
            "merek": sub_bag["merek"]
        })

        if not existing_document:
            # Insert the document if it does not exist
            ajukan_id = mongo.db.kepala_bagian.insert_one(
                {
                    "id_sub_bag": sub_bag["_id"],
                    "tanggal_pengusulan": sub_bag["tanggal_penerimaan"],
                    "tanggal_penerimaan": None,
                    "nama_barang": sub_bag["nama_barang"],
                    "volume": sub_bag["volume"],
                    "merek": sub_bag["merek"],
                    "ruangan": sub_bag["ruangan"],
                    "jumlah_diterima": 0,
                    "is_verif": False,
                    "status": "Process",
                }
            ).inserted_id

            # Retrieve the newly inserted document
            new_ajukan = mongo.db.kepala_bagian.find_one({"_id": ajukan_id})
            new_ajukan["_id"] = str(new_ajukan["_id"])
            new_documents.append(new_ajukan)
        else:
            # Document already exists, add it to the response without re-inserting
            existing_document["_id"] = str(existing_document["_id"])
            new_documents.append(existing_document)

    return jsonify({"kepala_bagian": new_documents}), 201


@kepala_bagian_bp.route("/ajukan/<ajukan_id>", methods=["GET"])
def get_ajukan(ajukan_id):
    ajukan_item = mongo.db.kepala_bagian.find_one({"_id": ObjectId(ajukan_id)})
    if not ajukan_item:
        return jsonify({"message": "Ajukan item not found"}), 404
    ajukan_item["_id"] = str(ajukan_item["_id"])
    return jsonify(ajukan_item)


@kepala_bagian_bp.route("/verifikasi", methods=["POST"])
def verifikasi():
    data = request.get_json()
    ajukan_id = data.get("id_ajukan")
    jumlah_diterima = data.get("jumlah_diterima")
    current_date = datetime.now().strftime("%Y-%m-%d")
    alasan = data.get("alasan")
    status = data.get("status")

    if not ajukan_id or jumlah_diterima is None:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        ajukan_id = ObjectId(ajukan_id)
    except Exception as e:
        return jsonify({"message": "Invalid id_ajukan format"}), 400

    ajukan = mongo.db.kepala_bagian.find_one({"_id": ajukan_id})
    if not ajukan:
        return jsonify({"message": "Invalid id_ajukan"}), 400

    pipeline = [
        {
            '$lookup': {
                'from': 'categories',
                'localField': 'kategori_id',
                'foreignField': '_id',
                'as': 'category_info'
            }
        },
        {
            '$unwind': '$category_info'
        },
        {
            '$match': {
                'nama_barang': ajukan['nama_barang']
            }
        }
    ]
    barang = list(_items_collection.aggregate(pipeline))
    if barang:
        barang_item = barang[0]
        new_stok_tersedia = barang_item['stock_tersedia'] - int(ajukan['jumlah'])

        # Update the 'barang' item
        _items_collection.update_one(
            {'_id': barang_item['_id']},
            {'$set': {'stock_tersedia': new_stok_tersedia}}
        )
    else:
       return (
            jsonify({"message": "Barang not found"}),
            400,
        )

    volume = int(ajukan["volume"])

    if int(jumlah_diterima) > volume:
        return jsonify({"message": "Jumlah diterima cannot be greater than volume"}), 400

    is_verif = int(jumlah_diterima) == volume

    result = mongo.db.kepala_bagian.update_one(
        {"_id": ajukan_id},
        {
            "$set": {
                "jumlah_diterima": jumlah_diterima,
                "is_verif": is_verif,
                "tanggal_penerimaan": current_date,
                "status": status,
                "alasan": alasan,
            }
        },
    )
    if result.modified_count == 1:
        return jsonify({"message": "Verification completed successfully"})
    else:
        # Added logging for debugging
        print("Failed to update document with id: %s", ajukan_id)
        return jsonify({"message": "Verification failed"}), 500

@kepala_bagian_bp.route("/verifikasi_true", methods=["GET"])
def get_verified_ajukan():
    verified_items = list(mongo.db.kepala_bagian.find({"is_verif": True}))
    for item in verified_items:
        item["_id"] = str(item["_id"])
    return jsonify({"verified_kepala_bagian": verified_items})


@kepala_bagian_bp.route("/verifikasi_false", methods=["GET"])
def get_unverified_ajukan():
    unverified_items = list(mongo.db.kepala_bagian.find({"is_verif": False}))
    for item in unverified_items:
        item["_id"] = str(item["_id"])
    return jsonify({"unverified_kepala_bagian": unverified_items})
