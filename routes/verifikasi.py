from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from models import mongo
from datetime import datetime
from pymongo import MongoClient, DESCENDING

verifikasi_bp = Blueprint("api/verifikasi", __name__, url_prefix="/api/verifikasi")

_client = MongoClient('mongodb://selvi:selvi@ac-ou90izj-shard-00-00.37a1b2k.mongodb.net:27017,ac-ou90izj-shard-00-01.37a1b2k.mongodb.net:27017,ac-ou90izj-shard-00-02.37a1b2k.mongodb.net:27017/?ssl=true&replicaSet=atlas-4a46gy-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0')
_db = _client['inventory_app'] # Ganti dengan nama database Anda
_items_collection = _db['items']

# @verifikasi_bp.route("/ajukan", methods=["POST"])
# def ajukan():
#     data = request.get_json()
#     id_kepala_bagian = data.get("id_kepala_bagian")

#     if not id_kepala_bagian:
#         return jsonify({"message": "Missing required field id_kepala_bagian"}), 400

#     kepala_bagian = mongo.db.kepala_bagian.find_one(
#         {"_id": ObjectId(id_kepala_bagian), "is_verif": True}
#     )
#     if not kepala_bagian:
#         return jsonify({"message": "Invalid or unverified id_kepala_bagian"}), 400

#     ajukan_id = mongo.db.verifikasi.insert_one(
#         {
#             "id_kepala_bagian": id_kepala_bagian,
#             "tanggal_pengusulan": kepala_bagian["tanggal_penerimaan"],
#             "tanggal_penerimaan": None,
#             "nama_barang": kepala_bagian["nama_barang"],
#             "volume": kepala_bagian["volume"],
#             "merek": kepala_bagian["merek"],
#             "ruangan": kepala_bagian["ruangan"],
#             "jumlah_diterima": 0,
#             "is_verif": False,
#             "status": "Proses",
#         }
#     ).inserted_id

#     new_ajukan = mongo.db.verifikasi.find_one({"_id": ajukan_id})
#     new_ajukan["_id"] = str(new_ajukan["_id"])

#     return jsonify(new_ajukan), 201


@verifikasi_bp.route("/ajukan", methods=["GET"])
def ajukan():
    # Retrieve all items that are verified from kepala_bagian collection
    verified_items = list(mongo.db.kepala_bagian.find({"is_verif": True}))
    new_documents = []

    for sub_bag in verified_items:
        # Check if the document already exists in verifikasi
        existing_document = mongo.db.verifikasi.find_one({
            "id_kepala_bagian": str(sub_bag["_id"]),
            "tanggal_pengusulan": sub_bag["tanggal_penerimaan"],
            "nama_barang": sub_bag["nama_barang"],
            "volume": sub_bag["volume"],
            "merek": sub_bag["merek"]
        })

        if not existing_document:
            # Insert the document if it does not exist
            ajukan_id = mongo.db.verifikasi.insert_one(
                {
                    "id_kepala_bagian": str(sub_bag["_id"]),
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

            # Retrieve the newly inserted document from verifikasi collection
            new_ajukan = mongo.db.verifikasi.find_one({"_id": ajukan_id})
            new_ajukan["_id"] = str(new_ajukan["_id"])  # Convert _id to string for JSON serialization
            new_documents.append(new_ajukan)
        else:
            # Document already exists, add it to the response without re-inserting
            existing_document["_id"] = str(existing_document["_id"])
            new_documents.append(existing_document)

    return jsonify({"verifikasi": new_documents}), 201
    # Retrieve all items that are verified from kepala_bagian collection
    verified_items = list(mongo.db.kepala_bagian.find({"is_verif": True}))
    new_documents = []

    for sub_bag in verified_items:
        # Insert each verified item into the verifikasi collection
        ajukan_id = mongo.db.verifikasi.insert_one(
            {
                "id_kepala_bagian": str(
                    sub_bag["_id"]
                ),  # Store the _id of kepala_bagian
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

        # Retrieve the newly inserted document from verifikasi collection
        new_ajukan = mongo.db.verifikasi.find_one({"_id": ajukan_id})
        new_ajukan["_id"] = str(
            new_ajukan["_id"]
        )  # Convert _id to string for JSON serialization
        new_documents.append(new_ajukan)

    return jsonify({"verifikasi": new_documents}), 201


@verifikasi_bp.route("/ajukan", methods=["GET"])
def get_all_ajukan():
    ajukan_items = list(mongo.db.verifikasi.find())
    for item in ajukan_items:
        item["_id"] = str(item["_id"])
    return jsonify({"verifikasi": ajukan_items})


@verifikasi_bp.route("/ajukan/<ajukan_id>", methods=["GET"])
def get_ajukan(ajukan_id):
    ajukan_item = mongo.db.verifikasi.find_one({"_id": ObjectId(ajukan_id)})
    if not ajukan_item:
        return jsonify({"message": "Ajukan item not found"}), 404
    
    # Extract ruangan and tanggal_pengusulan from the found item
    ruangan = ajukan_item.get("ruangan")
    tanggal_pengusulan = ajukan_item.get("tanggal_pengusulan")
    
    # Find all items with the same ruangan and tanggal_pengusulan
    similar_items = list(mongo.db.verifikasi.find({
        "ruangan": ruangan,
        "tanggal_pengusulan": tanggal_pengusulan
    }))
    
    # Convert ObjectId to string for all items
    for item in similar_items:
        item["_id"] = str(item["_id"])
    
    return jsonify(similar_items)



@verifikasi_bp.route("/verif", methods=["POST"])
def verifikasi():
    data = request.get_json()
    print(data)
    ajukan_id = data.get("id_ajukan")
    jumlah_diterima = data.get("jumlah_diterima")
    # Get the current date in YYYY-MM-DD format
    current_date = datetime.now().strftime("%Y-%m-%d")
    alasan = data.get("alasan")
    status = data.get("status")

    if not ajukan_id or jumlah_diterima is None:
        return jsonify({"message": "Missing required fields"}), 400

    ajukan = mongo.db.verifikasi.find_one({"_id": ObjectId(ajukan_id)})
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
        return (
            jsonify({"message": "Jumlah diterima cannot be greater than volume"}),
            400,
        )

    is_verif = jumlah_diterima == volume

    result = mongo.db.verifikasi.update_one(
        {"_id": ObjectId(ajukan_id)},
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
        }
    ]
    barang = list(items_collection.aggregate(pipeline))

    # if status == "Decline":
    #     mongo.db.sub_bag.update_one(
    #         {"_id": ObjectId(ajukan_id)},
    #         {
    #             "$set": {
    #                 "jumlah_diterima": jumlah_diterima,
    #                 "is_verif": is_verif,
    #                 "status": status,
    #                 "alasan": alasan,
    #             }
    #         },
    #     )


    if result.modified_count == 1:
        return jsonify({"message": "Verification completed successfully"})
    else:
        return jsonify({"message": "Verification failed"}), 500


@verifikasi_bp.route("/verifikasi_true", methods=["GET"])
def get_verified_ajukan():
    verified_items = list(mongo.db.verifikasi.find({"is_verif": True}))
    for item in verified_items:
        item["_id"] = str(item["_id"])
    return jsonify({"verified_verifikasi": verified_items})


@verifikasi_bp.route("/verifikasi_false", methods=["GET"])
def get_unverified_ajukan():
    unverified_items = list(mongo.db.verifikasi.find({"is_verif": False}))
    for item in unverified_items:
        item["_id"] = str(item["_id"])
    return jsonify({"unverified_verifikasi": unverified_items})
