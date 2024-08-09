from flask import Blueprint, request, jsonify
from bson import ObjectId
from models import mongo
from datetime import datetime
from pymongo import MongoClient, DESCENDING

staff_gudang_bp = Blueprint(
    "api/staff_gudang", __name__, url_prefix="/api/staff_gudang"
)

_client = MongoClient('mongodb://selvi:selvi@ac-ou90izj-shard-00-00.37a1b2k.mongodb.net:27017,ac-ou90izj-shard-00-01.37a1b2k.mongodb.net:27017,ac-ou90izj-shard-00-02.37a1b2k.mongodb.net:27017/?ssl=true&replicaSet=atlas-4a46gy-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0')
_db = _client['inventory_app'] # Ganti dengan nama database Anda
_items_collection = _db['items']

@staff_gudang_bp.route("/ajukan", methods=["POST"])
def ajukan():
    data = request.get_json()
    print(data)
    id_pengajuan_barang = data.get("id_pengajuan_barang")

    if not id_pengajuan_barang:
        return jsonify({"message": "Missing required fields"}), 400

    # Fetch the pengajuan_barang document
    pengajuan_barang = mongo.db.pengajuan_barang.find_one(
        {"_id": ObjectId(id_pengajuan_barang)}
    )

    if not pengajuan_barang:
        return jsonify({"message": "Pengajuan Barang not found"}), 404

    # Extract details from the referenced document
    tanggal_pengajuan = pengajuan_barang.get("tanggal_pengajuan")
    nama_barang = pengajuan_barang.get("nama_barang")
    jumlah = pengajuan_barang.get("jumlah")
    ruangan = pengajuan_barang.get("ruangan")
    status = "Process"

    # Check if the document already exists in staff_gudang
    existing_document = mongo.db.staff_gudang.find_one({
        "id_pengajuan_barang": id_pengajuan_barang,
        "tanggal_pengajuan": tanggal_pengajuan,
        "nama_barang": nama_barang,
        "jumlah": jumlah,
        "ruangan": ruangan
    })

    if existing_document:
        return jsonify({"message": "Document already exists"}), 409

    # Insert the new document into staff_gudang
    staff_gudang_id = mongo.db.staff_gudang.insert_one(
        {
            "id_pengajuan_barang": id_pengajuan_barang,
            "tanggal_pengajuan": tanggal_pengajuan,
            "tanggal_penerimaan": None,
            "nama_barang": nama_barang,
            "jumlah": jumlah,
            "ruangan": ruangan,
            "jumlah_diterima": 0,  # Default value
            "is_verif": False,  # Set is_verif to False by default
            "status": status,
        }
    ).inserted_id

    # Delete the pengajuan_barang document after it is submitted
    mongo.db.pengajuan_barang.delete_one({"_id": ObjectId(id_pengajuan_barang)})
    
    new_sub_bag = mongo.db.staff_gudang.find_one({"_id": staff_gudang_id})
    new_sub_bag["_id"] = str(new_sub_bag["_id"])  # Convert ObjectId to string
    new_sub_bag["id_pengajuan_barang"] = str(
        new_sub_bag["id_pengajuan_barang"]
    )  # Ensure reference ID is also a string

    return jsonify(new_sub_bag), 201

@staff_gudang_bp.route("/ajukan", methods=["GET"])
def get_all_ajukan():
    staff_gudang_items = list(mongo.db.staff_gudang.find())

    for item in staff_gudang_items:
        item["_id"] = str(item["_id"])
        item["id_pengajuan_barang"] = str(item["id_pengajuan_barang"])

    return jsonify({"staff_gudang": staff_gudang_items}), 200


@staff_gudang_bp.route("/ajukan/<ajukan_id>", methods=["GET"])
def get_ajukan_detail(ajukan_id):
    staff_gudang_item = mongo.db.staff_gudang.find_one({"_id": ObjectId(ajukan_id)})

    if not staff_gudang_item:
        return jsonify({"message": "Ajukan not found"}), 404

    staff_gudang_item["_id"] = str(staff_gudang_item["_id"])
    staff_gudang_item["id_pengajuan_barang"] = str(
        staff_gudang_item["id_pengajuan_barang"]
    )

    return jsonify(staff_gudang_item), 200


@staff_gudang_bp.route("/verifikasi", methods=["POST"])
def verifikasi():
    data = request.get_json()
    ajukan_id = data.get("id_ajukan")
    alasan = data.get("alasan")
    jumlah_diterima = data.get("jumlah_diterima")
    current_date = datetime.now().strftime("%Y-%m-%d")

    if not ajukan_id or jumlah_diterima is None:
        return jsonify({"message": "Missing required fields"}), 400

    ajukan = mongo.db.staff_gudang.find_one({"_id": ObjectId(ajukan_id)})
    if not ajukan:
        return jsonify({"message": "Invalid id_ajukan"}), 400

    jumlah = int(ajukan["jumlah"])

    # If there is an 'alasan', set jumlah_diterima to 0
    if alasan:
        jumlah_diterima = 0
    elif jumlah_diterima > jumlah:
        return jsonify({"message": "Jumlah diterima cannot be greater than jumlah awal"}), 400

    is_verif = jumlah_diterima == jumlah

    if jumlah_diterima > 0:  # Only adjust stock if jumlah_diterima is greater than 0
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
            
            # Ensure correct stock adjustment
            if new_stok_tersedia < 0:
                new_stok_tersedia = 0  # Prevent negative stock

            update_result = _items_collection.update_one(
                {'_id': barang_item['_id']},
                {'$set': {'stock_tersedia': new_stok_tersedia}}
            )
            if update_result.modified_count == 0:
                return jsonify({"message": "Stock update failed"}), 500
        else:
            return jsonify({"message": "Barang not found"}), 400

    result = mongo.db.staff_gudang.update_one(
        {"_id": ObjectId(ajukan_id)},
        {
            "$set": {
                "jumlah_diterima": jumlah_diterima,
                "is_verif": is_verif,
                "tanggal_penerimaan": current_date,
                "alasan": alasan
            }
        },
    )

    if result.modified_count == 1:
        return jsonify({"message": "Verification completed successfully"})
    else:
        return jsonify({"message": "Verification failed"}), 500


@staff_gudang_bp.route("/verifikasi_true", methods=["GET"])
def get_verified_ajukan():
    verified_items = list(mongo.db.staff_gudang.find({"is_verif": True}))
    for item in verified_items:
        item["_id"] = str(item["_id"])
    return jsonify({"verified_staff_gudang": verified_items})


@staff_gudang_bp.route("/verifikasi_false", methods=["GET"])
def get_unverified_ajukan():
    unverified_items = list(mongo.db.staff_gudang.find({"is_verif": False}))
    for item in unverified_items:
        item["_id"] = str(item["_id"])
    return jsonify({"unverified_staff_gudang": unverified_items})
