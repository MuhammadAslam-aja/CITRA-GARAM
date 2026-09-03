import os
from app import app, response
from app.controller import AuthController, DashboardController, HomeController, PenggunaController, DatasetController, KlasifikasiController, RiwayatKlasifikasiController
from flask import request, send_file
from flask_login import login_required


@app.route('/', methods=['GET'])
def homes():
    return HomeController.index()

@app.route('/beranda/klasifikasi', methods=['GET', 'POST'])
def homeKlasifikasis():
    return HomeController.homeKlasifikasi()


@app.route('/login', methods=['GET', 'POST'])
def logins():
    return AuthController.login()


@app.route('/logout', methods=['POST', 'GET'])
def logouts():
    return AuthController.logout()


@app.route('/dashboard', methods=['GET'])
@login_required
def dashboards():
    return DashboardController.dashboard()

@app.route('/dashboard/stats', methods=['GET'])
@login_required
def getStats():
    return DashboardController.getStats()


@app.route('/pengguna', methods=['GET'])
@login_required
def penggunas():
    return PenggunaController.index()

@app.route('/pengguna/get-pengguna', methods=['GET'])
@login_required
def getPenggunas():
    return PenggunaController.getPengguna()

@app.route('/pengguna/add', methods=['GET', 'POST'])
@login_required
def addPenggunas():
    return PenggunaController.add()

@app.route('/pengguna/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def editPenggunas(id):
    return PenggunaController.edit(id)


@app.route('/pengguna/delete/<int:id>', methods=['DELETE'])
@login_required
def deletePenggunas(id):
    return PenggunaController.delete(id)

@app.route('/dataset', methods=['GET'])
@login_required
def datasets():
    return DatasetController.index()

@app.route('/dataset/get-dataset', methods=['GET'])
@login_required
def getDatasets():
    return DatasetController.getDataset()

@app.route("/dataset/view/<int:id>", methods=["GET"])
@login_required
def viewDataset(id):
    return DatasetController.viewDataset(id)

@app.route('/dataset/refresh-count', methods=['GET'])
@login_required
def getDatasetCount():
    return DatasetController.refreshCount()

@app.route('/dataset/upload', methods=['GET', 'POST'])
@login_required
def uploadDatasets():
    return DatasetController.upload()

@app.route('/dataset/delete/<int:id>', methods=['DELETE'])
@login_required
def deleteDatasets(id):
    return DatasetController.delete(id)

@app.route('/dataset/delete-all', methods=['DELETE'])
@login_required
def deleteAllDatasets():
    return DatasetController.deleteAll()

@app.route('/klasifikasi', methods=['GET', 'POST'])
@login_required
def klasifikasis():
    return KlasifikasiController.index()


@app.route('/hasil-klasifikasi', methods=['GET'])
@login_required
def resultKlasifikasis():
    return KlasifikasiController.result()


@app.route('/riwayat-klasifikasi', methods=['GET'])
@login_required
def riwayatKlasifikasis():
    return RiwayatKlasifikasiController.index()

@app.route('/riwayat-klasifikasi/get-klasifikasi', methods=['GET'])
@login_required
def getKlasifikasis():
    return RiwayatKlasifikasiController.getKlasifikasiHistory()

@app.route("/riwayat-klasifikasi/view/<int:id>", methods=["GET"])
@login_required
def viewKlasifikasi(id):
    return RiwayatKlasifikasiController.view(id)

@app.route('/riwayat-klasifikasi/delete-all', methods=['DELETE'])
@login_required
def deleteAllKlasifikasi():
    return RiwayatKlasifikasiController.deleteAll()


@app.route('/upload/<path:path>')
def access_file(path):
    file_path = os.path.abspath(f'upload/{path}')
    if not os.path.exists(file_path):
        return "File not found"
    return send_file(file_path)
