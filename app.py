from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)

from bson.objectid import ObjectId
from config import get_port, get_mongodb_uri
from models import bcrypt, mongo
from routes.auth import auth_bp
from routes.staffRuangan import staff_ruangan_bp
from routes.sub_bagian import sub_bagian_bp
from routes.kepala_bagian import kepala_bagian_bp
from routes.verifikasi import verifikasi_bp
from routes.transaksi import transaksi_bp
from routes.staff_gudang import staff_gudang_bp
from datetime import datetime
from collections import defaultdict
import requests
from pymongo import MongoClient, DESCENDING
import re
from bson import ObjectId


app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# Initialize database and bcrypt
app.config["MONGO_URI"] = get_mongodb_uri()
mongo.init_app(app)
bcrypt.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(staff_ruangan_bp)
app.register_blueprint(sub_bagian_bp)
app.register_blueprint(kepala_bagian_bp)
app.register_blueprint(verifikasi_bp)
app.register_blueprint(transaksi_bp)
app.register_blueprint(staff_gudang_bp)

import json
import requests

client = MongoClient('mongodb://selvi:selvi@ac-ou90izj-shard-00-00.37a1b2k.mongodb.net:27017,ac-ou90izj-shard-00-01.37a1b2k.mongodb.net:27017,ac-ou90izj-shard-00-02.37a1b2k.mongodb.net:27017/?ssl=true&replicaSet=atlas-4a46gy-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0')
db = client['inventory_app'] # Ganti dengan nama database Anda
items_collection = db['items']
  # Ganti dengan nama koleksi Anda

client2 = MongoClient('mongodb+srv://xyla:xyla@cluster0.fvn8oip.mongodb.net/RSUD_DR_Darsono')
db2 = client2['RSUD_DR_Darsono']

@app.route("/handle_login", methods=["POST"])
def handle_login():
    username = request.form.get("username")
    password = request.form.get("password")
    login_data = {"username": username, "password": password}

    print("JSON data:", json.dumps(login_data, indent=4))

    api_url = "http://127.0.0.1:5000/auth/login"
    response = requests.post(api_url, json=login_data)
    print(response)

    if response.status_code == 200:
        session["username"] = username
        # session["name"] = name
        login_response = response.json()
        role = login_response.get("role", None)
        username = login_response.get("username", None)
        # name = login_response.get("name", None)
        session["role"] = role

        # if re.match(r'^Staff Ruangan [A-Z]$', username):
        #     session["username"] = username
        #     return redirect("/staff_ruangan")
        if role.startswith('staffruangan'):
            session["username"] = username
            return redirect("/staff_ruangan")
        elif role == "kepalabidang":
            session["username"] = username
            return redirect("/kepala_bidang")
        elif role == "verifikasi":
            session["username"] = username
            return redirect("/verifikasi")
        elif role == "Staff Gudang":
            session["username"] = username
            return redirect("/staff_gudang")
        elif role == "subbagian":
            session["username"] = username
            return redirect("/sub_bag")

        else:
            flash("Invalid role for dashboard access.", "error")
            return redirect(url_for("login"))
    else:
        flash("Login failed. Please check your username and password.", "error")
        return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard-staff.html", username=session["username"])


@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


@app.route("/")
def index():
    return render_template("login.html", menu="home")


######################################
# Role Sub Bagian / Pejabat Keuangan #
######################################
@app.route("/sub_bag")
def dashboard_subBag():
    return render_template(
        "/pages/sub_bagian/dashboard_kepalaSubBag.html", menu="dashboard"
    )


@app.route("/sub_bag/verif", methods=["GET", "POST"])
def verifikasisubBag():
    if request.method == "POST":
        if request.form.get("_method") == "DELETE":
            return delete_pengusulan_barang(request.form.get("id"))

    # Fetch data from the API
    api_url = "http://127.0.0.1:5000/api/sub_bagian/ajukan"
    response = requests.get(api_url)
    data = response.json()

    # Extract the sub_bag data
    sub_bag = data.get("sub_bag", [])
    # Get the current date in YYYY-MM-DD format
    current_date = datetime.now().strftime("%Y-%m-%d")
    # Process data if necessary (e.g., adding additional fields)
    processed_data = []
    for i, item in enumerate(sub_bag):
        processed_data.append(
            {
                "no": i + 1,
                "tanggal": item["tanggal_pengusulan"],
                "ruangan": item["ruangan"],  # Adjust this according to your data
                "id": item["_id"],
                "is_verif": item["is_verif"],
                "jumlah_diterima": item["jumlah_diterima"],
                "merek": item["merek"],
                "nama_barang": item["nama_barang"],
                "tanggal_penerimaan": item["tanggal_penerimaan"],
                "volume": item["volume"],
            }
        )

    print("DATA DATA SUB BAGIAN:>>>>>>>>>>>>>>>")
    print(processed_data)
    return render_template(
        "/pages/sub_bagian/verifikasi_subBag.html",
        menu="verifikasi",
        data=processed_data,
    )


@app.route("/sub_bag/verif/detail/<item_id>")
def verifikasiDetailSubBag(item_id):
    api_url = f"http://127.0.0.1:5000/api/sub_bagian/ajukan/{item_id}"
    response = requests.get(api_url)
    item_detail = response.json()

    print("Ini adalah item detail")
    print(item_detail)

    return render_template(
        "/pages/sub_bagian/verifikasi-detail-subBag.html",
        menu="verifikasi",
        item_detail=item_detail,
    )


@app.route("/api/sub_bagian/verifikasi", methods=["POST"])
def verifikasi():
    try:
        data = request.get_json()
        print("DATA VERIFIKASIIIIIIIIII")
        print(data)

        # Extract fields from JSON data
        id_ajukan = str(
            data.get("id_ajukan")
        )  # Ensure id_ajukan is treated as a string
        reason = data.get("reason")
        jumlah_diterima = data.get("jumlah_diterima")

        # Validate if required fields are present
        if not id_ajukan:
            return jsonify({"message": "Missing 'id_ajukan' field"}), 400

        # Process the data as needed
        print(
            f"Received data: id_ajukan={id_ajukan}, jumlah_diterima={jumlah_diterima}, reason={reason}"
        )

        # Here you can perform further processing based on your business logic

        return jsonify({"message": "Verification successful", "results": data}), 200
    except Exception as e:
        # Log the exception for debugging purposes
        print(str(e))
        return jsonify({"message": "Verification failed", "error": str(e)}), 500

@app.route("/sub_bag/transaksi")
def transaksisubBag():
    tglstart = request.args.get('tglstart')
    tglend = request.args.get('tglend')
    ruangan = request.args.get('ruangan')
    
    query = {}
    
    if tglstart:
        query["tanggal_pengusulan"] = {"$gte": tglstart}
    
    if tglend:
        if "tanggal_pengusulan" in query:
            query["tanggal_pengusulan"]["$lte"] = tglend
        else:
            query["tanggal_pengusulan"] = {"$lte": tglend}
    
    if ruangan:
        query["ruangan"] = ruangan
    
    if query:
         data_cursor = list(mongo.db.sub_bag.find(query))
    else:
        data_cursor = list(mongo.db.sub_bag.find())
    aggregated_data = defaultdict(lambda: {
        "id": None,
        "no": None,
        "id_pengusulan_barang": None,
        "tanggal_pengusulan": None,
        "tanggal_penerimaan": None,
        "nama_barang": [],
        "volume": 0,
        "merek": [],
        "ruangan": None,
        "jumlah_diterima": 0,
        "is_verif": True,
        "status": None
    })
    
    for document in data_cursor:
        key = (document.get("id_pengusulan_barang"), document.get("tanggal_pengusulan"), document.get("tanggal_penerimaan"), document.get("ruangan"))
        entry = aggregated_data[key]
        
        entry["id"] = document.get("_id")  # Just an example, might need a unique identifier or sequential numbering
        entry["id_pengusulan_barang"] = document.get("id_pengusulan_barang")
        entry["tanggal_pengusulan"] = document.get("tanggal_pengusulan")
        entry["tanggal_penerimaan"] = document.get("tanggal_penerimaan")
        entry["nama_barang"].append(document.get("nama_barang"))
        entry["volume"] += int(document.get("volume"))
        entry["merek"].append(document.get("merek"))
        entry["ruangan"] = document.get("ruangan")
        entry["jumlah_diterima"] += int(document.get("jumlah_diterima"))
        entry["is_verif"] = entry["is_verif"] and document.get("is_verif")
        entry["status"] = document.get("status")

    data = []
    for index, (key, value) in enumerate(aggregated_data.items(), start=1):
        value["no"] = index
        value["nama_barang"] = ', '.join(value["nama_barang"])
        filtered_merek = [merek for merek in value["merek"] if merek is not None]
        value["merek"] = ', '.join(filtered_merek) if filtered_merek else '-'
        # value["merek"] = ', '.join(value["merek"])
        data.append(value)
    
    return render_template('/pages/sub_bagian/transaksi_subBag.html', data=data, menu="transaksi_verifikasi", tglstart=tglstart, tglend=tglend, ruangan=ruangan)

    # Fetch data from MongoDB
    data_cursor = list(mongo.db.kepala_bagian.find())
    aggregated_data = defaultdict(lambda: {
        "id" : None,
        "no": None,
        "id_kepala_bagian": None,
        "tanggal_pengusulan": None,
        "tanggal_penerimaan": None,
        "nama_barang": [],
        "volume": 0,
        "merek": [],
        "ruangan": None,
        "jumlah_diterima": 0,
        "is_verif": True,
        "status": None
    })
    
    for document in data_cursor:
        key = (document.get("id_kepala_bagian"), document.get("tanggal_pengusulan"), document.get("tanggal_penerimaan"), document.get("ruangan"))
        entry = aggregated_data[key]
        
        entry["id"] = document.get("_id")  # Just an example, might need a unique identifier or sequential numbering
        entry["id_kepala_bagian"] = document.get("id_kepala_bagian")
        entry["tanggal_pengusulan"] = document.get("tanggal_pengusulan")
        entry["tanggal_penerimaan"] = document.get("tanggal_penerimaan")
        entry["nama_barang"].append(document.get("nama_barang"))
        entry["volume"] += int(document.get("volume"))
        entry["merek"].append(document.get("merek"))
        entry["ruangan"] = document.get("ruangan")
        entry["jumlah_diterima"] += int(document.get("jumlah_diterima"))
        entry["is_verif"] = entry["is_verif"] and document.get("is_verif")
        entry["status"] = document.get("status")

    # Convert defaultdict to list
    data = []
    for index, (key, value) in enumerate(aggregated_data.items(), start=1):
        value["no"] = index
        value["nama_barang"] = ', '.join(value["nama_barang"])
        filtered_merek = [merek for merek in value["merek"] if merek is not None]
        value["merek"] = ', '.join(filtered_merek) if filtered_merek else '-'
        # value["merek"] = ', '.join(value["merek"])
        data.append(value)
    
    return render_template('/pages/kepala_bidang/transaksi_kepalaBidang.html', data=data, menu="transaksi_verifikasi")

@app.route("/sub_bag/transaksi/detail/<id>")
def subBagDetailTransaksi(id):
    # Fetch the document based on the provided ID
    document = mongo.db.sub_bag.find_one({"_id": ObjectId(id)})
    
    if not document:
        return "Document not found", 404
    
    # Fetch other documents that match the same id_pengusulan_barang, tanggal_pengusulan, tanggal_penerimaan, and ruangan
    filter_criteria = {
        "id_pengusulan_barang": document.get("id_pengusulan_barang"),
        "tanggal_pengusulan": document.get("tanggal_pengusulan"),
        "tanggal_penerimaan": document.get("tanggal_penerimaan"),
        "ruangan": document.get("ruangan"),
    }
    
    related_documents = list(mongo.db.sub_bag.find(filter_criteria))
    
    # Process related documents to prepare for the table
    items = []
    for idx, doc in enumerate(related_documents, start=1):
        items.append({
            "no": idx,
            "nama_barang": doc.get("nama_barang"),
            "volume": doc.get("volume"),
            "merek": doc.get("merek"),
            "status": doc.get("status"),
            "jumlah_diterima": doc.get("jumlah_diterima"),
        })
    print(items)
    return render_template(
        '/pages/sub_bagian/detail_transaksi_subBagian.html',
        document=document,
        items=items
    )


###################
# Role VERIFIKASI #
###################
@app.route("/verifikasi")
def dashboard_verifikasi():
    return render_template(
        "/pages/verifikasi/dashboard_verifikasi.html", menu="dashboard"
    )


@app.route("/verifikasi/verif", methods=["GET", "POST"])
def verifikasiverif():
    if request.method == "POST":
        if request.form.get("_method") == "DELETE":
            return delete_pengusulan_barang(request.form.get("id"))

    api_url = "http://127.0.0.1:5000/api/verifikasi/ajukan"
    response = requests.get(api_url)
    data = response.json()

    verifikasi = data.get("verifikasi", [])

    # Use a dictionary to filter unique entries based on 'ruangan' and 'tanggal_pengusulan'
    unique_entries = {}
    for item in verifikasi:
        key = (item["ruangan"], item["tanggal_pengusulan"])
        if key not in unique_entries:
            unique_entries[key] = item

    processed_data = []
    for i, item in enumerate(unique_entries.values()):
        processed_data.append(
            {
                "no": i + 1,
                "tanggal": item["tanggal_pengusulan"],
                "ruangan": item["ruangan"],
                "id": item["_id"],
                "is_verif": item["is_verif"],
                "jumlah_diterima": item["jumlah_diterima"],
                "merek": item["merek"],
                "nama_barang": item["nama_barang"],
                "tanggal_penerimaan": item["tanggal_penerimaan"],
                "volume": item["volume"],
            }
        )

    print("DATA DATA VERIFIKASI:>>>>>>>>>>>>>>>")
    print(processed_data)
    return render_template(
        "/pages/verifikasi/verifikasi-verifikasi.html",
        data=processed_data,
        menu="verifikasi4",
    )


@app.route("/verifikasi/verif/detail/<item_id>")
def verifikasiDetailVerifikasi(item_id):
    document = mongo.db.verifikasi.find_one({"_id": ObjectId(item_id)})
    print(document)
    
    if not document:
        return "Document not found", 404
    
    # Fetch other documents that match the same id_kepala_bagian, tanggal_pengusulan, tanggal_penerimaan, and ruangan
    filter_criteria = {
        "id_kepala_bagian": document.get("id_kepala_bagian"),
        "tanggal_pengusulan": document.get("tanggal_pengusulan"),
        "tanggal_penerimaan": document.get("tanggal_penerimaan"),
        "ruangan": document.get("ruangan"),
    }
    
    related_documents = list(mongo.db.verifikasi.find(filter_criteria))
    
    # Process related documents to prepare for the table
    items = []
    for idx, doc in enumerate(related_documents, start=1):
        items.append({
            "no": idx,
            "nama_barang": doc.get("nama_barang"),
            "volume": doc.get("volume"),
            "merek": doc.get("merek"),
            "status": doc.get("status"),
            "jumlah_diterima": doc.get("jumlah_diterima"),
        })

    return render_template(
        "/pages/verifikasi/verifikasi-detail-verifikasi.html",
        document=document,
        menu="verifikasi4",
        items=items,
    )

@app.route("/verifikasi/transaksi_verifikasi")
def transaksiVerifikasi():
    tglstart = request.args.get('tglstart')
    tglend = request.args.get('tglend')
    ruangan = request.args.get('ruangan')
    
    query = {}
    
    if tglstart:
        query["tanggal_pengusulan"] = {"$gte": tglstart}
    
    if tglend:
        if "tanggal_pengusulan" in query:
            query["tanggal_pengusulan"]["$lte"] = tglend
        else:
            query["tanggal_pengusulan"] = {"$lte": tglend}
    
    if ruangan:
        query["ruangan"] = ruangan
    
    if query:
         data_cursor = list(mongo.db.verifikasi.find(query))
    else:
        data_cursor = list(mongo.db.verifikasi.find())
    aggregated_data = defaultdict(lambda: {
        "id": None,
        "no": None,
        "id_kepala_bagian": None,
        "tanggal_pengusulan": None,
        "tanggal_penerimaan": None,
        "nama_barang": [],
        "volume": 0,
        "merek": [],
        "ruangan": None,
        "jumlah_diterima": 0,
        "is_verif": True,
        "status": None
    })
    
    for document in data_cursor:
        key = (document.get("id_kepala_bagian"), document.get("tanggal_pengusulan"), document.get("tanggal_penerimaan"), document.get("ruangan"))
        entry = aggregated_data[key]
        
        entry["id"] = document.get("_id")  # Just an example, might need a unique identifier or sequential numbering
        entry["id_kepala_bagian"] = document.get("id_kepala_bagian")
        entry["tanggal_pengusulan"] = document.get("tanggal_pengusulan")
        entry["tanggal_penerimaan"] = document.get("tanggal_penerimaan")
        entry["nama_barang"].append(document.get("nama_barang"))
        entry["volume"] += int(document.get("volume"))
        entry["merek"].append(document.get("merek"))
        entry["ruangan"] = document.get("ruangan")
        entry["jumlah_diterima"] += int(document.get("jumlah_diterima"))
        entry["is_verif"] = entry["is_verif"] and document.get("is_verif")
        entry["status"] = document.get("status")

    data = []
    for index, (key, value) in enumerate(aggregated_data.items(), start=1):
        value["no"] = index
        value["nama_barang"] = ', '.join(value["nama_barang"])
        filtered_merek = [merek for merek in value["merek"] if merek is not None]
        value["merek"] = ', '.join(filtered_merek) if filtered_merek else '-'
        # value["merek"] = ', '.join(value["merek"])
        data.append(value)
    
    return render_template('/pages/verifikasi/transaksi_verifikasi.html', data=data, menu="transaksi_verifikasi", tglstart=tglstart, tglend=tglend, ruangan=ruangan)

    # Fetch data from MongoDB
    data_cursor = list(mongo.db.verifikasi.find())
    aggregated_data = defaultdict(lambda: {
        "id" : None,
        "no": None,
        "id_kepala_bagian": None,
        "tanggal_pengusulan": None,
        "tanggal_penerimaan": None,
        "nama_barang": [],
        "volume": 0,
        "merek": [],
        "ruangan": None,
        "jumlah_diterima": 0,
        "is_verif": True,
        "status": None
    })
    
    for document in data_cursor:
        key = (document.get("id_kepala_bagian"), document.get("tanggal_pengusulan"), document.get("tanggal_penerimaan"), document.get("ruangan"))
        entry = aggregated_data[key]
        
        entry["id"] = document.get("_id")  # Just an example, might need a unique identifier or sequential numbering
        entry["id_kepala_bagian"] = document.get("id_kepala_bagian")
        entry["tanggal_pengusulan"] = document.get("tanggal_pengusulan")
        entry["tanggal_penerimaan"] = document.get("tanggal_penerimaan")
        entry["nama_barang"].append(document.get("nama_barang"))
        entry["volume"] += int(document.get("volume"))
        entry["merek"].append(document.get("merek"))
        entry["ruangan"] = document.get("ruangan")
        entry["jumlah_diterima"] += int(document.get("jumlah_diterima"))
        entry["is_verif"] = entry["is_verif"] and document.get("is_verif")
        entry["status"] = document.get("status")

    # Convert defaultdict to list
    data = []
    for index, (key, value) in enumerate(aggregated_data.items(), start=1):
        value["no"] = index
        value["nama_barang"] = ', '.join(value["nama_barang"])
        filtered_merek = [merek for merek in value["merek"] if merek is not None]
        value["merek"] = ', '.join(filtered_merek) if filtered_merek else '-'
        # value["merek"] = ', '.join(value["merek"])
        data.append(value)
    
    return render_template('/pages/verifikasi/transaksi_verifikasi.html', data=data, menu="transaksi_verifikasi")

@app.route("/verifikasi/riwayat_transaksi/detail/<id>")
def verifikasiDetailTransaksi(id):
    # Fetch the document based on the provided ID
    document = mongo.db.verifikasi.find_one({"_id": ObjectId(id)})
    
    if not document:
        return "Document not found", 404
    
    # Fetch other documents that match the same id_kepala_bagian, tanggal_pengusulan, tanggal_penerimaan, and ruangan
    filter_criteria = {
        "id_kepala_bagian": document.get("id_kepala_bagian"),
        "tanggal_pengusulan": document.get("tanggal_pengusulan"),
        "tanggal_penerimaan": document.get("tanggal_penerimaan"),
        "ruangan": document.get("ruangan"),
    }
    
    related_documents = list(mongo.db.verifikasi.find(filter_criteria))
    
    # Process related documents to prepare for the table
    items = []
    for idx, doc in enumerate(related_documents, start=1):
        items.append({
            "no": idx,
            "nama_barang": doc.get("nama_barang"),
            "volume": doc.get("volume"),
            "merek": doc.get("merek"),
            "status": doc.get("status"),
            "jumlah_diterima": doc.get("jumlah_diterima"),
        })
    
    return render_template(
        '/pages/verifikasi/detail_transaksi_verifikasi.html',
        document=document,
        items=items
    )

@app.route("/detail_transaksi_verifikasi")
def detail_transaksi_verifikasi():
    return render_template('pages/verifikasi/transaksi_verifikasi.html/detail_transaksi_verifikasi.html', menu='detail_transaksi_verifikasi')


########################################
# Role Kepala Bidang / Atasan Langsung #
########################################
@app.route("/kepala_bidang")
def dashboard_kepalaBidang():
    return render_template(
        "/pages/kepala_bidang/dashboard_kepalaBidang.html", menu="dashboard"
    )


@app.route("/kepala_bidang/verif", methods=["GET", "POST"])
def verifikasiKepalaBidang():
    if request.method == "POST":
        if request.form.get("_method") == "DELETE":
            return delete_pengusulan_barang(request.form.get("id"))

    # Fetch data from the API
    api_url = "http://127.0.0.1:5000/api/kepala_bagian/ajukan"
    response = requests.get(api_url)
    data = response.json()

    # Extract the sub_bag data
    kepala_bagian = data.get("kepala_bagian", [])

    # Process data if necessary (e.g., adding additional fields)
    processed_data = []
    for i, item in enumerate(kepala_bagian):
        processed_data.append(
            {
                "no": i + 1,
                "tanggal": item["tanggal_pengusulan"],
                "ruangan": item["ruangan"],  # Adjust this according to your data
                "id": item["_id"],
                "is_verif": item["is_verif"],
                "jumlah_diterima": item["jumlah_diterima"],
                "merek": item["merek"],
                "nama_barang": item["nama_barang"],
                "tanggal_penerimaan": item["tanggal_penerimaan"],
                "volume": item["volume"],
            }
        )

    return render_template(
        "/pages/kepala_bidang/verifikasi-kepalaBidang.html",
        data=processed_data,
        menu="verifikasi5",
    )


@app.route("/kepala_bidang/verif/detail/<item_id>")
def verifikasiDetailkepalaBidang(item_id):
    api_url = f"http://127.0.0.1:5000/api/kepala_bagian/ajukan/{item_id}"
    response = requests.get(api_url)
    item_detail = response.json()

    return render_template(
        "/pages/kepala_bidang/verifikasi-detail-kepalaBidang.html",
        menu="verifikasi5",
        item_detail=item_detail,
    )

@app.route("/kepala_bidang/report_informatif", methods=["GET", "POST"])
def reportInformatif():
    bulan = request.args.get('bulan')
    param_bulan = request.args.get('bulan')

    filter_conditions = {
        'is_verif': True,
        'status': {'$in': ['Process', 'Success']}
    }

    if not bulan:
        bulan = datetime.now().strftime('%Y-%m')

    if bulan:
        try:
            tahun, bulan = bulan.split('-')
            start_date = f"{tahun}-{bulan}-01"
            if int(bulan) == 12:
                end_date = f"{int(tahun) + 1}-01-01"
            else:
                end_date = f"{tahun}-{int(bulan) + 1:02d}-01"

            filter_conditions['$or'] = [
                {'tanggal_pengajuan': {'$gte': start_date, '$lt': end_date}},
                {'tanggal_penerimaan': {'$gte': start_date, '$lt': end_date}}
            ]
        except ValueError:
            return jsonify({'message': 'Format bulan tidak valid!'}), 400

    # Fetch data for Pengajuan
    data_pengajuan = list(mongo.db.pengajuan_barang.find(filter_conditions))
    data_staff_gudang = list(mongo.db.staff_gudang.find(filter_conditions))

    # Fetch data for Pengusulan
    data_kepala_bagian = list(mongo.db.kepala_bagian.find(filter_conditions))
    data_verifikasi = list(mongo.db.verifikasi.find(filter_conditions))
    data_sub_bag = list(mongo.db.sub_bag.find(filter_conditions))

    # Combine and group data by ruangan
    combined_pengajuan = data_pengajuan + data_staff_gudang
    combined_pengusulan = data_kepala_bagian + data_verifikasi + data_sub_bag

    pengajuan_by_ruangan = {}
    for item in combined_pengajuan:
        ruangan = item.get('ruangan', 'Unknown')
        if ruangan not in pengajuan_by_ruangan:
            pengajuan_by_ruangan[ruangan] = 0
        pengajuan_by_ruangan[ruangan] += 1

    pengusulan_by_ruangan = {}
    for item in combined_pengusulan:
        ruangan = item.get('ruangan', 'Unknown')
        if ruangan not in pengusulan_by_ruangan:
            pengusulan_by_ruangan[ruangan] = 0
        pengusulan_by_ruangan[ruangan] += 1

    # Prepare the data for rendering
    report_data = []
    all_ruangan = set(pengajuan_by_ruangan.keys()).union(set(pengusulan_by_ruangan.keys()))
    for ruangan in all_ruangan:
        report_data.append({
            'ruangan': ruangan,
            'total_pengajuan': pengajuan_by_ruangan.get(ruangan, 0),
            'total_pengusulan': pengusulan_by_ruangan.get(ruangan, 0)
        })

    # Sort the report data by 'ruangan' in ascending order
    report_data = sorted(report_data, key=lambda x: x['ruangan'])

    indonesian_date = ""

    if param_bulan:
        # Parse the date
        date_obj = datetime.strptime(param_bulan, "%Y-%m")

        # Format the date to "Juli 2024"
        formatted_date = date_obj.strftime("%B %Y")

        # Translate the month to Indonesian
        months_translation = {
            "January": "Januari",
            "February": "Februari",
            "March": "Maret",
            "April": "April",
            "May": "Mei",
            "June": "Juni",
            "July": "Juli",
            "August": "Agustus",
            "September": "September",
            "October": "Oktober",
            "November": "November",
            "December": "Desember"
        }

        indonesian_date = months_translation[formatted_date.split()[0]] + " " + formatted_date.split()[1]

    return render_template(
        "/pages/kepala_bidang/report-informatif.html",
        menu="report_informatif",
        param_bulan=param_bulan,
        transactions=report_data,
        indonesian_date=indonesian_date 
    )


@app.route("/detail_transaksi_kepalaBidang")
def detail_transaksi_kepalaBidang():
    return render_template('pages/kepala_bidang/transaksi_kepalaBidang.html/detail_transaksi_kepalaBidang.html', menu='detail_transaksi_kepalaBidang')

@app.route("/kepala_bidang/transaksi")
def transaksiKepalaBidang():
    tglstart = request.args.get('tglstart')
    tglend = request.args.get('tglend')
    ruangan = request.args.get('ruangan')
    
    query = {}
    
    if tglstart:
        query["tanggal_pengusulan"] = {"$gte": tglstart}
    
    if tglend:
        if "tanggal_pengusulan" in query:
            query["tanggal_pengusulan"]["$lte"] = tglend
        else:
            query["tanggal_pengusulan"] = {"$lte": tglend}
    
    if ruangan:
        query["ruangan"] = ruangan
    
    if query:
         data_cursor = list(mongo.db.kepala_bagian.find(query))
    else:
        data_cursor = list(mongo.db.kepala_bagian.find())
    aggregated_data = defaultdict(lambda: {
        "id": None,
        "no": None,
        "id_sub_bag": None,
        "tanggal_pengusulan": None,
        "tanggal_penerimaan": None,
        "nama_barang": [],
        "volume": 0,
        "merek": [],
        "ruangan": None,
        "jumlah_diterima": 0,
        "is_verif": True,
        "status": None
    })
    
    for document in data_cursor:
        key = (document.get("id_sub_bag"), document.get("tanggal_pengusulan"), document.get("tanggal_penerimaan"), document.get("ruangan"))
        entry = aggregated_data[key]
        
        entry["id"] = document.get("_id")  # Just an example, might need a unique identifier or sequential numbering
        entry["id_sub_bag"] = document.get("id_sub_bag")
        entry["tanggal_pengusulan"] = document.get("tanggal_pengusulan")
        entry["tanggal_penerimaan"] = document.get("tanggal_penerimaan")
        entry["nama_barang"].append(document.get("nama_barang"))
        entry["volume"] += int(document.get("volume"))
        entry["merek"].append(document.get("merek"))
        entry["ruangan"] = document.get("ruangan")
        entry["jumlah_diterima"] += int(document.get("jumlah_diterima"))
        entry["is_verif"] = entry["is_verif"] and document.get("is_verif")
        entry["status"] = document.get("status")

    data = []
    for index, (key, value) in enumerate(aggregated_data.items(), start=1):
        value["no"] = index
        value["nama_barang"] = ', '.join(value["nama_barang"])
        filtered_merek = [merek for merek in value["merek"] if merek is not None]
        value["merek"] = ', '.join(filtered_merek) if filtered_merek else '-'
        # value["merek"] = ', '.join(value["merek"])
        data.append(value)
    
    return render_template('/pages/kepala_bidang/transaksi_kepalaBidang.html', data=data, menu="transaksi_verifikasi", tglstart=tglstart, tglend=tglend, ruangan=ruangan)

    # Fetch data from MongoDB
    data_cursor = list(mongo.db.kepala_bagian.find())
    aggregated_data = defaultdict(lambda: {
        "id" : None,
        "no": None,
        "id_kepala_bagian": None,
        "tanggal_pengusulan": None,
        "tanggal_penerimaan": None,
        "nama_barang": [],
        "volume": 0,
        "merek": [],
        "ruangan": None,
        "jumlah_diterima": 0,
        "is_verif": True,
        "status": None
    })
    
    for document in data_cursor:
        key = (document.get("id_kepala_bagian"), document.get("tanggal_pengusulan"), document.get("tanggal_penerimaan"), document.get("ruangan"))
        entry = aggregated_data[key]
        
        entry["id"] = document.get("_id")  # Just an example, might need a unique identifier or sequential numbering
        entry["id_kepala_bagian"] = document.get("id_kepala_bagian")
        entry["tanggal_pengusulan"] = document.get("tanggal_pengusulan")
        entry["tanggal_penerimaan"] = document.get("tanggal_penerimaan")
        entry["nama_barang"].append(document.get("nama_barang"))
        entry["volume"] += int(document.get("volume"))
        entry["merek"].append(document.get("merek"))
        entry["ruangan"] = document.get("ruangan")
        entry["jumlah_diterima"] += int(document.get("jumlah_diterima"))
        entry["is_verif"] = entry["is_verif"] and document.get("is_verif")
        entry["status"] = document.get("status")

    # Convert defaultdict to list
    data = []
    for index, (key, value) in enumerate(aggregated_data.items(), start=1):
        value["no"] = index
        value["nama_barang"] = ', '.join(value["nama_barang"])
        filtered_merek = [merek for merek in value["merek"] if merek is not None]
        value["merek"] = ', '.join(filtered_merek) if filtered_merek else '-'
        # value["merek"] = ', '.join(value["merek"])
        data.append(value)
    
    return render_template('/pages/kepala_bidang/transaksi_kepalaBidang.html', data=data, menu="transaksi_verifikasi")

@app.route("/kepala_bidang/transaksi/detail/<id>")
def kepalaBidangDetailTransaksi(id):
    # Fetch the document based on the provided ID
    document = mongo.db.kepala_bagian.find_one({"_id": ObjectId(id)})
    
    if not document:
        return "Document not found", 404
    
    # Fetch other documents that match the same id_sub_bag, tanggal_pengusulan, tanggal_penerimaan, and ruangan
    filter_criteria = {
        "id_sub_bag": document.get("id_sub_bag"),
        "tanggal_pengusulan": document.get("tanggal_pengusulan"),
        "tanggal_penerimaan": document.get("tanggal_penerimaan"),
        "ruangan": document.get("ruangan"),
    }
    
    related_documents = list(mongo.db.kepala_bagian.find(filter_criteria))
    print(related_documents)
    
    # Process related documents to prepare for the table
    items = []
    for idx, doc in enumerate(related_documents, start=1):
        items.append({
            "no": idx,
            "nama_barang": doc.get("nama_barang"),
            "volume": doc.get("volume"),
            "merek": doc.get("merek"),
            "status": doc.get("status"),
            "jumlah_diterima": doc.get("jumlah_diterima"),
        })
    print(items)
    return render_template(
        '/pages/verifikasi/detail_transaksi_verifikasi.html',
        document=document,
        items=items
    )


################
# Staff Gudang #
################
@app.route("/staff_gudang")
def dashboard_gudang():
    return render_template(
        "/pages/staff_gudang/dashboard_gudang.html", menu="dashboard"
    )

@app.route("/staff_gudang/verif")
def verifikasi_pengajuan():
    if request.method == "POST":
        if request.form.get("_method") == "DELETE":
            return delete_pengusulan_barang(request.form.get("id"))

    # Fetch data from the API
    api_url = "http://127.0.0.1:5000/api/staff_gudang/ajukan"
    response = requests.get(api_url)
    data = response.json()

    # Extract the sub_bag data
    verif = data.get("staff_gudang", [])

    print("DATA DATA STAFFGUDANG: lllllll>>>>>>>>>>>>>>>")
    print(verif)
    # Process data if necessary (e.g., adding additional fields)
    processed_data = []
    for i, item in enumerate(verif):
        processed_data.append(
            {
                "no": i + 1,
                "tanggal": item["tanggal_pengajuan"],
                "ruangan": item["ruangan"],  # Adjust this according to your data
                "id": item["_id"],
                "is_verif": item["is_verif"],
                "jumlah_diterima": item["jumlah_diterima"],
                "nama_barang": item["nama_barang"],
                "tanggal_penerimaan": item["tanggal_penerimaan"],
            }
        )

    print("DATA DATA STAFFGUDANG: gudang>>>>>>>>>>>>>>>")
    print(processed_data)

    return render_template(
        "/pages/staff_gudang/verifikasi_pengajuan.html",
        data=processed_data,
        menu="verifikasi_pengajuan",
    )

@app.route("/staff_gudang/verif/detail/<item_id>")
def verifikasi_detail_pengajuan(item_id):
    api_url = f"http://127.0.0.1:5000/api/staff_gudang/ajukan/{item_id}"
    response = requests.get(api_url)
    item_detail = response.json()
    print("DATA DATA STAFFGUDANG: VERIF>>>>>>>>>>>>>>>")
    print(item_detail)

    return render_template(
        "/pages/staff_gudang/verifikasi-detail-pengajuan.html",
        menu="verifikasi_pengajuan",
        item_detail=item_detail,
    )

@app.route('/staff_gudang/transaksi', methods=['GET'])
def transaksiGudang():
    api_url = "http://127.0.0.1:5000/api/transaksi"
    response = requests.get(api_url)
    data = response.json()

    tglstart = request.args.get('tglstart')
    tglend = request.args.get('tglend')
    ruangan = request.args.get('ruangan')

    transactions = []
    seen_transactions = set()

    # Helper function to check date range and room filter
    def filter_transaction(transaksi, date_key):
        if tglstart and transaksi[date_key] < tglstart:
            return False
        if tglend and transaksi[date_key] > tglend:
            return False
        if ruangan and transaksi.get('ruangan') != ruangan:
            return False
        return True

    # Helper function to create a unique key for each transaction
    def create_unique_key(transaksi, date_key, jenis_transaksi):
        return (transaksi[date_key], transaksi['ruangan'], jenis_transaksi)

    # Process pengajuan_barang
    for transaksi in data.get("pengajuan_barang", []):
        if filter_transaction(transaksi, "tanggal_pengajuan"):
            unique_key = create_unique_key(transaksi, "tanggal_pengajuan", "pengajuan_barang")
            if unique_key not in seen_transactions:
                seen_transactions.add(unique_key)
                transactions.append(
                    {
                        "no": transaksi["_id"],
                        "tanggal": transaksi["tanggal_pengajuan"],
                        "status": transaksi["status"],
                        "nama_barang": transaksi["nama_barang"],
                        "jumlah": transaksi["jumlah"],
                        "ruangan": transaksi["ruangan"],
                        "jenis_transaksi": "pengajuan_barang",
                    }
                )
    
    # Process pengusulan
    for transaksi in data.get("pengusulan", []):
        if filter_transaction(transaksi, "tanggal_pengusulan"):
            unique_key = create_unique_key(transaksi, "tanggal_pengusulan", "pengusulan")
            if unique_key not in seen_transactions:
                seen_transactions.add(unique_key)
                transactions.append(
                    {
                        "no": transaksi["_id"],
                        "tanggal": transaksi["tanggal_pengusulan"],
                        "status": transaksi["status"],
                        "nama_barang": transaksi["nama_barang"],
                        "jumlah": transaksi["jumlah_diterima"],
                        "ruangan": transaksi["ruangan"],
                        "jenis_transaksi": "pengusulan",
                    }
                )

    return render_template(
        "/pages/staff_gudang/transaksi_gudang.html",
        data=transactions,
        menu="transaksi_gudang",
        tglstart=tglstart,
        tglend=tglend,
        ruangan=ruangan,
    )
@app.route("/staff_gudang/transaksi/detail/<id>")
def detail_transaksi_gudang(id):
    # Define collections to search
    collections = ["staff_gudang", "sub_bag", "kepala_bagian", "verifikasi"]
    
    # Initialize the document variable
    document = None

    # Iterate over the collections to find the document
    for collection in collections:
        document = mongo.db[collection].find_one({"_id": ObjectId(id)})
        if document:
            break

    if not document:
        return "Document not found", 404

    # Build the filter criteria based on available fields in the document
    filter_criteria = {"ruangan": document.get("ruangan")}

    if "tanggal_pengajuan" in document:
        filter_criteria["tanggal_pengajuan"] = document.get("tanggal_pengajuan")
    if "tanggal_penerimaan" in document:
        filter_criteria["tanggal_penerimaan"] = document.get("tanggal_penerimaan")
    if "tanggal_pengusulan" in document:
        filter_criteria["tanggal_pengusulan"] = document.get("tanggal_pengusulan")
    
    # Fetch related documents from all relevant collections
    related_documents = []
    for collection in collections:
        related_documents += list(mongo.db[collection].find(filter_criteria))

    # Process related documents to prepare for the table
    items = []
    for idx, doc in enumerate(related_documents, start=1):
        items.append({
            "no": idx,
            "nama_barang": doc.get("nama_barang"),
            "jumlah": doc.get("jumlah", doc.get("volume", 0)),  # Use 'jumlah' or 'volume' based on the collection
            "status": doc.get("status"),
            "jumlah_diterima": doc.get("jumlah_diterima", 0),
        })

    return render_template(
        '/pages/staff_gudang/detail_transaksiGudang.html',
        document=document,
        items=items,
        menu="detail_transaksi_gudang"
    )

#################################
# Role Staff atau Staff Ruangan #
#################################

@app.route("/staff_ruangan")
def dashboardStaff():
    role = session['role']
    username = session['username']
    return render_template(
        "/pages/staff_ruangan/dashboard-staff.html", menu="dashboard", role=role, username=username
    )

@app.route("/staff_ruangan/stock")
def stock():
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
    
    items = list(items_collection.aggregate(pipeline))
    return render_template("/pages/staff_ruangan/stock.html", items=items)
# def find_ruangan_by_role(role):
#     if re.match(r'Staff Ruangan [A-Z]', role):
#         return role[-1]  # Mengambil karakter terakhir dari role seperti A, B, C, dst.
#     else:
#         return None

def find_ruangan_by_role(username):
    match = re.match(r'Ruangan (.+)', username)
    if match:
        return match.group(1).strip()  # Mengambil nama ruangan setelah 'Staff Ruangan'
    else:
        return None

@app.route("/staff_ruangan/transaksi")
def transaksiStaffRuangan():
    if 'role' not in session:
        return "Anda harus login untuk mengakses halaman ini"

    role = session['role']  # Ambil role pengguna dari session
    username = session['username']  # Ambil role pengguna dari session
    user_collection = db['users'] 
    user_data_cursor = user_collection.find_one({"username": username})
    if user_data_cursor:
        name = user_data_cursor.get('name')
        print(name)

    ruangan_user = find_ruangan_by_role(name)
    if not ruangan_user:
        return "Role pengguna tidak valid atau tidak memiliki akses ke ruangan manapun"

    tglstart = request.args.get('tglstart')
    tglend = request.args.get('tglend')
    jenis_layanan = request.args.get('jenis_layanan')
    ruangan_user = "Mawar"  # Example value; adjust accordingly

    query = {
        "ruangan": ruangan_user  # Filter berdasarkan ruangan sesuai role pengguna
    }

    date_conditions = []

    if tglstart:
        date_conditions.append({"tanggal_pengusulan": {"$gte": tglstart}})
        date_conditions.append({"tanggal_pengajuan": {"$gte": tglstart}})

    if tglend:
        date_conditions.append({"tanggal_pengusulan": {"$lte": tglend}})
        date_conditions.append({"tanggal_pengajuan": {"$lte": tglend}})

    if date_conditions:
        query["$or"] = date_conditions

    def fetch_data(jenis_layanan, query):
        if jenis_layanan == "pengajuan":
            return {
                "data_pengajuan": list(mongo.db.pengajuan_barang.find(query)),
                "data_staff_gudang": list(mongo.db.staff_gudang.find(query))
            }
        elif jenis_layanan == "pengusulan":
            return {
                "data_kepala_bagian": list(mongo.db.kepala_bagian.find(query)),
                "data_verifikasi": list(mongo.db.verifikasi.find(query)),
                "data_sub_bag": list(mongo.db.sub_bag.find(query))
            }
        else:
            return {
                "data_pengajuan": list(mongo.db.pengajuan_barang.find(query)),
                "data_staff_gudang": list(mongo.db.staff_gudang.find(query)),
                "data_kepala_bagian": list(mongo.db.kepala_bagian.find(query)),
                "data_verifikasi": list(mongo.db.verifikasi.find(query)),
                "data_sub_bag": list(mongo.db.sub_bag.find(query))
            }

    def aggregate_data(data):
        unique_entries = set()
        aggregated_data = defaultdict(lambda: {
            "id": "",
            "tanggal": None,
            "nama_barang": [],
            "volume": 0,
            "merek": [],
            "ruangan": "",
            "jumlah_diterima": 0,
            "is_verif": True,
            "status": ""
        })

        unique_entries = set()

        for collection_name, documents in data.items():
            for document in documents:
                if document.get("is_verif") != True:
                    continue

                tanggal = None
                if collection_name in ["data_kepala_bagian", "data_verifikasi", "data_sub_bag"]:
                    tanggal = document.get("tanggal_pengusulan")
                elif collection_name in ["data_staff_gudang", "data_pengajuan"]:
                    tanggal = document.get("tanggal_pengajuan")
                else:
                    tanggal = document.get("tanggal_pengusulan") or document.get("tanggal_pengajuan") or document.get("tanggal_penerimaan")

                ruangan = document.get("ruangan")
                unique_key = (tanggal, ruangan, collection_name)

                if unique_key not in unique_entries:
                    unique_entries.add(unique_key)

                if collection_name in ["data_kepala_bagian", "data_verifikasi", "data_sub_bag"]:
                    key = (document.get("tanggal_pengusulan"), document.get("ruangan"))
                elif collection_name in ["data_staff_gudang", "data_pengajuan"]:
                    key = (document.get("tanggal_pengajuan"), document.get("ruangan"))
                else:
                    key = (document.get("id_sub_bag"), document.get("tanggal_pengusulan"), document.get("tanggal_penerimaan"), document.get("ruangan"))
                
                entry = aggregated_data[key]

                entry["id"] = str(document.get("_id"))
                entry["tanggal"] = tanggal
                entry["nama_barang"].append(document.get("nama_barang"))
                entry["volume"] += int(document.get("volume") or document.get("jumlah", 0))
                entry["merek"].append(document.get("merek"))
                entry["ruangan"] = ruangan
                entry["jumlah_diterima"] += int(document.get("jumlah_diterima", 0))
                entry["is_verif"] = entry["is_verif"] and document.get("is_verif", True)
                entry["status"] = document.get("status")

                if (collection_name in ["data_staff_gudang", "data_pengajuan"]) and document.get("status") == "Process":
                    entry["status"] = "Success"

        return list(aggregated_data.values())

    data = fetch_data(jenis_layanan, query)
    aggregated_result = aggregate_data(data)

    # Example output
    print("Aggregated Result:")
    for item in aggregated_result:
        print(item)

    return render_template('/pages/staff_ruangan/transaksi.html', data=aggregated_result, menu="transaksi_verifikasi", tglstart=tglstart, tglend=tglend, jenis_layanan=jenis_layanan,role=role, username=username)

# Fungsi untuk mengambil data transaksi berdasarkan role pengguna
# @app.route("/staff_ruangan/transaksi")
# def transaksiStaffRuangan():
    # if 'role' not in session:
    #     return "Anda harus login untuk mengakses halaman ini"

    # role_user = session['role']  # Ambil role pengguna dari session

    # ruangan_user = find_ruangan_by_role(role_user)
    # if not ruangan_user:
    #     return "Role pengguna tidak valid atau tidak memiliki akses ke ruangan manapun"

    # tglstart = request.args.get('tglstart')
    # tglend = request.args.get('tglend')
    # jenis_layanan = request.args.get('jenis_layanan')

    # query = {
    #     "ruangan": ruangan_user  # Filter berdasarkan ruangan sesuai role pengguna
    # }

    # if tglstart:
    #     query["tanggal_pengusulan"] = {"$gte": tglstart}

    # if tglend:
    #     if "tanggal_pengusulan" in query:
    #         query["tanggal_pengusulan"]["$lte"] = tglend
    #     else:
    #         query["tanggal_pengusulan"] = {"$lte": tglend}

    # data_cursor = []

    # if jenis_layanan == "pengajuan":
    #     data_cursor = list(mongo.db.pengajuan_barang.find(query))
    # elif jenis_layanan == "pengusulan":
    #     data_cursor = list(mongo.db.kepala_bagian.find(query)) + \
    #                   list(mongo.db.verifikasi.find(query)) + \
    #                   list(mongo.db.sub_bag.find(query))
    # else:
    #     data_cursor = list(mongo.db.kepala_bagian.find(query)) + \
    #                   list(mongo.db.sub_bag.find(query)) + \
    #                   list(mongo.db.pengajuan_barang.find(query)) + \
    #                   list(mongo.db.verifikasi.find(query))

    # # To track unique entries by tanggal and ruangan
    # unique_entries = set()
    # aggregated_data = defaultdict(lambda: {
    #     "id": None,
    #     "no": None,
    #     "tanggal": None,
    #     "nama_barang": [],
    #     "volume": 0,
    #     "merek": [],
    #     "ruangan": None,
    #     "jumlah_diterima": 0,
    #     "is_verif": True,
    #     "status": None,
    # })

    # for document in data_cursor:
    #     tanggal = document.get("tanggal_pengusulan") or document.get("tanggal_pengajuan") or document.get("tanggal_penerimaan")
    #     ruangan = document.get("ruangan")
    #     unique_key = (tanggal, ruangan)

    #     if unique_key not in unique_entries:
    #         unique_entries.add(unique_key)

    #         key = (document.get("id_sub_bag"), document.get("tanggal_pengusulan"), document.get("tanggal_penerimaan"), document.get("ruangan"))
    #         entry = aggregated_data[key]

    #         entry["id"] = str(document.get("_id"))
    #         entry["tanggal"] = tanggal
    #         entry["nama_barang"].append(document.get("nama_barang"))
    #         entry["volume"] += int(document.get("volume") or document.get("jumlah", 0))
    #         entry["merek"].append(document.get("merek"))
    #         entry["ruangan"] = ruangan
    #         entry["jumlah_diterima"] += int(document.get("jumlah_diterima", 0))
    #         entry["is_verif"] = entry["is_verif"] and document.get("is_verif", True)
    #         entry["status"] = document.get("status")

    # data = []
    # for index, (key, value) in enumerate(aggregated_data.items(), start=1):
    #     value["no"] = index
    #     value["nama_barang"] = ', '.join(value["nama_barang"])
    #     value["merek"] = ', '.join(value["merek"])
    #     data.append(value)

    # return render_template('/pages/staff_ruangan/transaksi.html', data=data, menu="transaksi_verifikasi", tglstart=tglstart, tglend=tglend, jenis_layanan=jenis_layanan)

@app.route("/staff_ruangan/transaksi/detail/<id>")
def staffRuanganDetailTransaksi(id):
    from bson import ObjectId, errors
    from flask import render_template

    # Verifikasi ID
    try:
        document_id = ObjectId(id)
    except errors.InvalidId:
        return "Invalid ID format", 400

    # Koleksi
    staff_gudang_collection = db2['staff_gudang']
    sub_bag_collection= db2['sub_bag']
    kepala_bagian_collection = db2['kepala_bagian']
    

    # Cari dokumen dsub_bag_collectioni staff_gudang
    document = staff_gudang_collection.find_one({"_id": document_id})

    checkStaffGudangC = staff_gudang_collection.find_one({"_id": document_id})
    checkSubBagC = sub_bag_collection.find_one({"_id": document_id})
    checkKepalaBagianC = kepala_bagian_collection.find_one({"_id": document_id})


    if checkStaffGudangC:
        document = checkStaffGudangC
    if checkSubBagC:
        document = checkSubBagC
    if checkKepalaBagianC:
        document = checkKepalaBagianC


    # Filter kriteria untuk dokumen terkait
    filter_criteria = {}

    related_documents = list(kepala_bagian_collection.find(filter_criteria))

    if checkStaffGudangC:
        print("A")
        filter_criteria = {
        "id_sub_bag": document.get("id_pengusulan_barang"),
        # "tanggal_pengusulan": document.get("tanggal_pengusulan") if document.get("tanggal_pengusulan") else document.get("tanggal_pengajuan"),
        "tanggal_penerimaan": document.get("tanggal_penerimaan"),
        # "ruangan": document.get("ruangan"),'
        }
        related_documents = list(staff_gudang_collection.find(filter_criteria))
    if checkSubBagC:
        print("B")
        filter_criteria = {
        # "id_sub_bag": document.get("id_pengusulan_barang"),
        "tanggal_pengusulan": document.get("tanggal_pengusulan") if document.get("tanggal_pengusulan") else document.get("tanggal_pengajuan"),
        # "tanggal_penerimaan": document.get("tanggal_penerimaan"),
        # "ruangan": document.get("ruangan"),
        "status": "Success"
        }
        related_documents = list(sub_bag_collection.find(filter_criteria))
    if checkKepalaBagianC:
        print("C")
        filter_criteria = {
        # "id_sub_bag": document.get("id_pengusulan_barang"),
        "tanggal_pengusulan": document.get("tanggal_pengusulan") if document.get("tanggal_pengusulan") else document.get("tanggal_pengajuan"),
        "tanggal_penerimaan": document.get("tanggal_penerimaan"),
        "ruangan": document.get("ruangan"),
        }
        related_documents = list(kepala_bagian_collection.find(filter_criteria))

    if not document:
        return "Document not found", 404

    print("Filter criteria:", filter_criteria)

    # Cari dokumen terkait

    
    # Siapkan data untuk ditampilkan di template
    items = []
    for idx, doc in enumerate(related_documents, start=1):
        items.append({
            "no": idx,
            "nama_barang": doc.get("nama_barang"),
            "volume": doc.get("volume"),
            "merek": doc.get("merek"),
            "status": doc.get("status"),
            "jumlah_diterima": doc.get("jumlah_diterima", 0),
        })

    # Debugging print
    print("related_documents: ", related_documents)
    print("Document:", document)
    print("Items:", items)

    return render_template(
        '/pages/staff_ruangan/detail_transaksiRuangan.html',
        document=document,
        items=items
    )





@app.route("/staff_ruangan/pengajuan")
def pengajuanBarang():
    role = session['role']  # Ambil role pengguna dari session
    user_collection = db['users']  # Koleksi yang menyimpan data pengguna
    username = session['username']
    user_collection = db['users'] 
    user_data_cursor = user_collection.find_one({"username": username})
    if user_data_cursor:
        name = user_data_cursor.get('name')
        print(name)


    if request.method == "POST":
        if request.form.get("_method") == "DELETE":
            return delete_pengajuan_barang(request.form.get("id"))
    api_url = "http://127.0.0.1:5000/api/staff_ruangan/pengajuan_barang"
    response = requests.get(api_url)
    data = response.json()
    items = items_collection.find()
    items_list = list(items)
    # print(items_list)
    pengajuan_barang = data.get("pengajuan_barang", [])

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
    
    def serialize_item(item):
        for key, value in item.items():
            if isinstance(value, ObjectId):
                item[key] = str(value)
            elif isinstance(value, list):
                item[key] = [serialize_item(sub_item) if isinstance(sub_item, dict) else sub_item for sub_item in value]
            elif isinstance(value, dict):
                item[key] = serialize_item(value)
        return item

    barang = [serialize_item(item) for item in barang]

    return render_template(
        "/pages/staff_ruangan/pengajuan-barang.html",
        items = items_list,
        menu="pengajuan-barang",
        pengajuan_barang=pengajuan_barang,
        role=role,
        username=name,
        barang=barang
    )

@app.route("/staff_ruangan/pengajuan", methods=["POST"])
def sendPengajuanBarang():
    role = session.get("role")
    if request.method == "POST":
        # Get the current date in YYYY-MM-DD format
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Retrieve form data
        nama_barang = request.form.get("nama_barang")
        jumlah = request.form.get("jumlah")
        ruangan = request.form.get("ruangan")

        # try:
        #     jumlah = int(jumlah)  # Konversi jumlah menjadi integer
        #     if jumlah <= 0:  # Memeriksa apakah jumlah kurang dari atau sama dengan 0
        #         return jsonify({"error": "Jumlah harus lebih dari 0"}), 400
        # except ValueError:
        #     return jsonify({"error": "Jumlah harus berupa angka"}), 400
    

        # Prepare data to be sent
        data = {
            "role": role,
            "tanggal_pengajuan": current_date,  # Use current date
            "nama_barang": nama_barang,
            "jumlah": jumlah,
            "ruangan": ruangan,
        }

        api_url = "http://127.0.0.1:5000/api/staff_ruangan/pengajuan_barang"
        response = requests.post(api_url, json=data)
        # print("JSON data:", json.dumps(data, indent=4))

        if response.status_code == 200:
            flash("Pengajuan barang berhasil diajukan.", "success")
        else:
            flash("Terjadi kesalahan saat mengajukan barang.", "error")

        return redirect(url_for("pengajuanBarang"))

@app.route("/staff_ruangan/pengajuan_barang/<string:item_id>", methods=["DELETE"])
def delete_pengajuan_barang(item_id):
    api_url = f"http://127.0.0.1:5000/api/staff_ruangan/pengajuan_barang/{item_id}"
    response = requests.delete(api_url)
    if response.status_code == 200:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": response.text}), response.status_code


@app.route("/staff_ruangan/pengajuan_barang/<string:item_id>", methods=["PUT"])
def update_pengajuan_barang(item_id):
    data = request.get_json()
    api_url = f"http://127.0.0.1:5000/api/staff_ruangan/pengajuan_barang/{item_id}"
    response = requests.put(api_url, json=data)
    if response.status_code == 200:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": response.text}), response.status_code

@app.route("/staff_ruangan/pengusulan")
def pengusulanBarang():
    if request.method == "POST":
        if request.form.get("_method") == "DELETE":
            return delete_pengajuan_barang(request.form.get("id"))
    api_url = "http://127.0.0.1:5000/api/staff_ruangan/pengusulan_barang"
    response = requests.get(api_url)
    data = response.json()
    print(data)

    pengusulan_barang = data.get("pengusulan_barang", [])
    print(pengusulan_barang)

    username = session['username']
    user_collection = db['users'] 
    user_data_cursor = user_collection.find_one({"username": username})
    if user_data_cursor:
        name = user_data_cursor.get('name')
        print(name)
    nama_ruangan_arr = name.split()
    nama_ruangan = nama_ruangan_arr[1]

    return render_template(
        "/pages/staff_ruangan/pengusulan_barang.html",
        menu="pengusulan_barang",
        pengusulan_barang=pengusulan_barang,
        username=username,
        nama_ruangan=nama_ruangan
    )

@app.route("/staff_ruangan/pengusulan", methods=["POST"])
def sendPengusulanBarang():
    role = session.get("role")
    
    if request.method == "POST":
        nama_barang = request.form.get("nama_barang")
        jumlah = request.form.get("jumlah")
        ruangan = request.form.get("ruangan")
        merek = request.form.get("merek")
        # Get the current date in YYYY-MM-DD format
        current_date = datetime.now().strftime("%Y-%m-%d")

        data = {
            "role": role,
            "tanggal_pengusulan": current_date,
            "nama_barang": nama_barang,
            "volume": jumlah,
            "ruangan": ruangan,
            "merek": merek,
        }

        api_url = "http://127.0.0.1:5000/api/staff_ruangan/pengusulan_barang"
        response = requests.post(api_url, json=data)
        print("JSON data:", json.dumps(data, indent=4))

        if response.status_code == 200:
            flash("Pengajuan barang berhasil diajukan.", "success")
        else:
            flash("Terjadi kesalahan saat mengajukan barang.", "error")

        return redirect(url_for("pengusulanBarang"))

@app.route("/staff_ruangan/pengusulan_barang/<string:item_id>", methods=["DELETE"])
def delete_pengusulan_barang(item_id):
    api_url = f"http://127.0.0.1:5000/api/staff_ruangan/pengusulan_barang/{item_id}"
    response = requests.delete(api_url)
    if response.status_code == 200:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": response.text}), response.status_code

@app.route("/staff_ruangan/pengusulan_barang/<string:item_id>", methods=["PUT"])
def update_pengusulan_barang(item_id):
    data = request.get_json()
    api_url = f"http://127.0.0.1:5000/api/staff_ruangan/pengusulan_barang/{item_id}"
    response = requests.put(api_url, json=data)
    if response.status_code == 200:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": response.text}), response.status_code

if __name__ == "__main__":
    app.run(debug=True)
