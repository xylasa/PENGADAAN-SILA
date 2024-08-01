from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from datetime import datetime

bcrypt = Bcrypt()
mongo = PyMongo()

# User model functions
def create_user(username, role, password):
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    user_id = mongo.db.users.insert_one(
        {"username": username, "role": role, "password": hashed_password}
    ).inserted_id
    return mongo.db.users.find_one({"_id": user_id})

# PengajuanBarang model functions
def create_pengajuan_barang(id_user, nama_barang, tanggal_pengajuan, tanggal_penerimaan, jumlah, ruangan):
    pengajuan_id = mongo.db.pengajuan_barang.insert_one(
        {
            "id_user": id_user,
            "nama_barang": nama_barang,
            "tanggal_pengajuan": datetime.strptime(tanggal_pengajuan, '%Y-%m-%d'),
            "tanggal_penerimaan": datetime.strptime(tanggal_penerimaan, '%Y-%m-%d'),
            "jumlah": jumlah,
            "ruangan": ruangan
        }
    ).inserted_id
    return mongo.db.pengajuan_barang.find_one({"_id": pengajuan_id})

# PengusulanBarang model functions
def create_pengusulan_barang(id_user, nama_barang, tanggal_pengusulan, tanggal_penerimaan, volume, merek, ruangan, id_sub_bag):
    pengusulan_id = mongo.db.pengusulan_barang.insert_one(
        {
            "id_user": id_user,
            "nama_barang": nama_barang,
            "tanggal_pengusulan": datetime.strptime(tanggal_pengusulan, '%Y-%m-%d'),
            "tanggal_penerimaan": datetime.strptime(tanggal_penerimaan, '%Y-%m-%d'),
            "volume": volume,
            "merek": merek,
            "ruangan": ruangan,
            "id_sub_bag": id_sub_bag
        }
    ).inserted_id
    return mongo.db.pengusulan_barang.find_one({"_id": pengusulan_id})

# Transaksi model functions
def create_transaksi(id_pengajuan, tanggal_penerimaan_pengajuan, is_verif_pengajuan, id_pengusulan, tanggal_penerimaan_pengusulan, is_verif_pengusulan):
    transaksi_id = mongo.db.transaksi.insert_one(
        {
            "id_pengajuan": id_pengajuan,
            "tanggal_penerimaan_pengajuan": datetime.strptime(tanggal_penerimaan_pengajuan, '%Y-%m-%d'),
            "is_verif_pengajuan": is_verif_pengajuan,
            "id_pengusulan": id_pengusulan,
            "tanggal_penerimaan_pengusulan": datetime.strptime(tanggal_penerimaan_pengusulan, '%Y-%m-%d'),
            "is_verif_pengusulan": is_verif_pengusulan
        }
    ).inserted_id
    return mongo.db.transaksi.find_one({"_id": transaksi_id})
