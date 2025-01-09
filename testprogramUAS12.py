import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import os
import webbrowser
import json
import requests

class Admin:
    def __init__(self, username, password):
        self.username = username
        self.password = password

class Paket:
    def __init__(self, id, pengirim, penerima, asal, tujuan, panjang, lebar, tinggi, berat, jarak, pengiriman, ongkir, tanggal_penambahan, estimasi_sampai, map_url, status="Menunggu konfirmasi", kurir=None):
        self.id = id
        self.pengirim = pengirim
        self.penerima = penerima
        self.asal = asal
        self.tujuan = tujuan
        self.panjang = panjang
        self.lebar = lebar
        self.tinggi = tinggi
        self.dimensi = f"{panjang} x {lebar} x {tinggi}"
        self.berat = berat
        self.jarak = round(jarak, 2) 
        self.pengiriman = pengiriman
        self.ongkir = round(ongkir, 2)
        self.status = status
        self.kurir = kurir
        self.tanggal_penambahan = tanggal_penambahan
        self.estimasi_sampai = estimasi_sampai
        self.map_url = map_url

class Kurir:
    def __init__(self, id, nama):
        self.id = id
        self.nama = nama

class DataStore:
    def __init__(self):
        self.paket_list = []
        self.kurir_list = []
        self.admin_list = []
        self.paket_id_counter = 1
        self.kurir_id_counter = 1
        self.load_data()

    def tambah_paket(self, paket):
        self.paket_list.append(paket)
        self.save_data()

    def tambah_kurir(self, kurir):
        self.kurir_list.append(kurir)
        self.save_data()

    def tambah_admin(self, admin):
        self.admin_list.append(admin)
        self.save_data()

    def autentikasi_admin(self, username, password):
        return next((a for a in self.admin_list if a.username == username and a.password == password), None)
    
    def update_paket(self, paket):
        for i, p in enumerate(self.paket_list):
            if p.id == paket.id:
                self.paket_list[i] = paket
                break
        self.save_data()
    
    def save_data(self):
        data = {
            "admins": [{"username": a.username, "password": a.password} for a in self.admin_list],
            "kurirs": [{"id": k.id, "nama": k.nama} for k in self.kurir_list],
            "pakets": [{
                "id": p.id,
                "pengirim": p.pengirim,
                "penerima": p.penerima,
                "asal": p.asal,
                "tujuan": p.tujuan,
                "panjang": p.panjang,
                "lebar": p.lebar,
                "tinggi": p.tinggi,
                "berat": p.berat,
                "jarak": p.jarak,
                "pengiriman": p.pengiriman,
                "ongkir": p.ongkir,
                "tanggal_penambahan": p.tanggal_penambahan.strftime('%Y-%m-%d %H:%M:%S'),
                "estimasi_sampai": p.estimasi_sampai.strftime('%Y-%m-%d %H:%M:%S'),
                "map_url": p.map_url,
                "status": p.status,
                "kurir": p.kurir
            } for p in self.paket_list]
        }
        with open("data.json", "w") as file:
            json.dump(data, file, indent=4)

    def load_data(self):
        try:
            with open("data.json", "r") as file:
                data = json.load(file)
                self.admin_list = [Admin(a["username"], a["password"]) for a in data.get("admins", [])]
                self.kurir_list = [Kurir(k["id"], k["nama"]) for k in data.get("kurirs", [])]
                self.paket_list = [
                    Paket(
                        p["id"],
                        p["pengirim"],
                        p["penerima"],
                        p["asal"],
                        p["tujuan"],
                        p["panjang"],
                        p["lebar"],
                        p["tinggi"],
                        p["berat"],
                        p["jarak"],
                        p["pengiriman"],
                        p["ongkir"],
                        datetime.strptime(p["tanggal_penambahan"], '%Y-%m-%d %H:%M:%S'),
                        datetime.strptime(p["estimasi_sampai"], '%Y-%m-%d %H:%M:%S'),
                        p["map_url"],
                        p["status"],
                        p["kurir"]
                    ) for p in data.get("pakets", [])
                ]
                self.paket_id_counter = max((p.id for p in self.paket_list), default=0) + 1
                self.kurir_id_counter = max((k.id for k in self.kurir_list), default=0) + 1
        except FileNotFoundError:
            with open("data.json", "w") as file:
                json.dump({"admins": [], "kurirs": [], "pakets": []}, file, indent=4)
            self.admin_list = []
            self.kurir_list = []
            self.paket_list = []


class PengirimanPaketApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Package Delivery System")
        self.root.geometry("800x600")

        # Base directory
        base_dir = os.path.dirname(os.path.abspath(__file__))

        self.root.configure(bg="#0f1a2b")

        # Icon jendela
        icon_path = os.path.join(base_dir, "image", "bluepaket.png")
        icon = PhotoImage(file=icon_path)
        self.root.iconphoto(True, icon)

        # Styling ttk
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#0f1a2b", font=("Helvetica", 12), foreground="white")
        style.configure("TButton",background="white", foreground="black", font=("Verdana", 10), padding=5)
        style.configure("Treeview.Heading", background="#0096c7", foreground="white")
        style.map("TButton", background=[("active", "#45b6fe")])

        self.store = DataStore()
        self.base_url = "http://router.project-osrm.org"
        self.geolocator = Nominatim(user_agent="pengiriman_paket")

        self.check_initial_admin()

    def check_initial_admin(self):
        if not self.store.admin_list:
            self.show_create_admin()
        else:
            self.show_main_menu()

    def show_create_admin(self):
        self.clear_window()

        ttk.Label(self.root, text="Buat Akun Admin", font=("Helvetica", 16, "bold"), foreground="white").pack(pady=10)
        ttk.Label(self.root, text="Username").pack(pady=5)
        username_entry = ttk.Entry(self.root)
        username_entry.pack(pady=5)
        ttk.Label(self.root, text="Password").pack(pady=5)
        password_entry = ttk.Entry(self.root, show="*")
        password_entry.pack(pady=5)

        def create_admin():
            username = username_entry.get()
            password = password_entry.get()
            if username and password:
                self.store.tambah_admin(Admin(username, password))
                messagebox.showinfo("Sukses", "Akun admin berhasil dibuat.")
                self.show_main_menu()
            else:
                messagebox.showerror("Error", "Username dan password tidak boleh kosong.")

        ttk.Button(self.root, text="Buat Akun", command=create_admin).pack(pady=20)

    def show_main_menu(self):
        self.clear_window()

        ttk.Label(self.root, text="Menu Utama", font=("Helvetica", 16, "bold"), foreground="white").pack(pady=10)
        ttk.Button(self.root, text="Menu Admin", command=self.show_admin_login).pack(pady=5)
        ttk.Button(self.root, text="Menu Pengguna", command=self.show_user_menu).pack(pady=5)

    def show_admin_login(self):
        self.clear_window()

        ttk.Label(self.root, text="Login Admin", font=("Helvetica", 16, "bold"), foreground="white").pack(pady=10)
        ttk.Label(self.root, text="Username").pack(pady=5)
        username_entry = ttk.Entry(self.root)
        username_entry.pack(pady=5)
        ttk.Label(self.root, text="Password").pack(pady=5)
        password_entry = ttk.Entry(self.root, show="*")
        password_entry.pack(pady=5)

        def authenticate():
            username = username_entry.get()
            password = password_entry.get()
            if self.store.autentikasi_admin(username, password):
                messagebox.showinfo("Login Berhasil", f"Selamat datang, {username}!")
                self.show_admin_menu()
            else:
                messagebox.showerror("Login Gagal", "Username atau password salah.")

        ttk.Button(self.root, text="LOGIN", command=authenticate).pack(pady=20)

    def show_admin_menu(self):
        self.clear_window()

        ttk.Label(self.root, text="Menu Admin", font=("Helvetica", 16, "bold"), foreground="white").pack(pady=10)
        ttk.Button(self.root, text="Tambah Admin", command=self.add_admin).pack(pady=5)
        ttk.Button(self.root, text="Tambah Kurir", command=self.add_kurir).pack(pady=5)
        ttk.Button(self.root, text="Lihat dan Kelola Paket", command=self.view_paket_admin).pack(pady=5)
        ttk.Button(self.root, text="Kembali", command=self.show_main_menu).pack(pady=20)

    def add_admin(self):
        def submit_admin():
            username = username_entry.get()
            password = password_entry.get()
            if username and password:
                self.store.tambah_admin(Admin(username, password))
                messagebox.showinfo("Sukses", f"Admin '{username}' berhasil ditambahkan.")
                admin_window.destroy()
            else:
                messagebox.showerror("Error", "Username dan password tidak boleh kosong.")

        admin_window = tk.Toplevel(self.root)
        admin_window.title("Tambah Admin")
        admin_window.configure(bg="#0096c7")
        ttk.Label(admin_window, text="Username", background="#0096c7").pack(pady=5)
        username_entry = ttk.Entry(admin_window)
        username_entry.pack(pady=5)
        ttk.Label(admin_window, text="Password", background="#0096c7").pack(pady=5)
        password_entry = ttk.Entry(admin_window, show="*")
        password_entry.pack(pady=5)
        ttk.Button(admin_window, text="Tambah", command=submit_admin).pack(pady=10)

    def add_kurir(self):
        def submit_kurir():
            nama = kurir_name_entry.get()
            if nama:
                kurir = Kurir(self.store.kurir_id_counter, nama)
                self.store.tambah_kurir(kurir)
                messagebox.showinfo("Sukses", f"Kurir '{nama}' dengan ID {self.store.kurir_id_counter} berhasil ditambahkan.")
                self.store.kurir_id_counter += 1
                kurir_window.destroy()
            else:
                messagebox.showerror("Error", "Nama kurir tidak boleh kosong.")

        kurir_window = tk.Toplevel(self.root)
        kurir_window.title("Tambah Kurir")
        kurir_window.configure(bg="#0096c7")
        ttk.Label(kurir_window, text="Nama Kurir", background="#0096c7").pack(pady=5)
        kurir_name_entry = ttk.Entry(kurir_window)
        kurir_name_entry.pack(pady=5)
        ttk.Button(kurir_window, text="Tambah", command=submit_kurir).pack(pady=10)

    def view_paket_admin(self):
        def refresh_list():
            for row in paket_tree.get_children():
                paket_tree.delete(row)
            for paket in self.store.paket_list:
                paket_tree.insert("", "end", values=(paket.id, paket.pengirim, paket.penerima, paket.asal, paket.tujuan, paket.dimensi, paket.berat, paket.jarak, paket.pengiriman, paket.ongkir, paket.tanggal_penambahan.strftime('%Y-%m-%d %H:%M:%S'), paket.estimasi_sampai.strftime('%Y-%m-%d %H:%M:%S'), paket.map_url, paket.status, paket.kurir))

        def update_status():
            selected_item = paket_tree.selection()
            if selected_item:
                item = paket_tree.item(selected_item)
                paket_id = int(item['values'][0])
                paket = self.store.paket_list[paket_id - 1]
                new_status = status_combobox.get()
                if new_status:
                    paket.status = new_status
                    refresh_list()
                    self.store.save_data()
                    messagebox.showinfo("Sukses", f"Status paket ID {paket.id} diperbarui menjadi '{paket.status}'.")

        def assign_kurir():
            selected_item = paket_tree.selection()
            if selected_item:
                item = paket_tree.item(selected_item)
                paket_id = int(item['values'][0])
                paket = self.store.paket_list[paket_id - 1]
                kurir_name = kurir_combobox.get()
                if kurir_name:
                    paket.kurir = kurir_name
                    refresh_list()
                    self.store.save_data()
                    messagebox.showinfo("Sukses", f"Kurir '{kurir_name}' berhasil ditugaskan untuk paket ID {paket.id}.")

        paket_window = tk.Toplevel(self.root)
        paket_window.title("Kelola Paket (Admin)")
        paket_window.configure(bg="#0f1a2b")

        paket_tree = ttk.Treeview(paket_window, columns=("ID", "Pengirim", "Penerima", "Asal", "Tujuan", "Dimensi", "Berat", "Jarak", "Pengiriman", "Ongkir", "Tanggal Pembuatan", "Estimasi Sampai", "Map", "Status", "Kurir"), show="headings")
        paket_tree.heading("ID", text="ID")
        paket_tree.heading("Pengirim", text="Pengirim")
        paket_tree.heading("Penerima", text="Penerima")
        paket_tree.heading("Asal", text="Asal")
        paket_tree.heading("Tujuan", text="Tujuan")
        paket_tree.heading("Dimensi", text="Dimensi")
        paket_tree.heading("Berat", text="Berat")
        paket_tree.heading("Jarak", text="Jarak (km)")
        paket_tree.heading("Pengiriman", text="Pengiriman")
        paket_tree.heading("Ongkir", text="Ongkir (Rp)")
        paket_tree.heading("Tanggal Pembuatan", text="Tanggal Pembuatan")
        paket_tree.heading("Estimasi Sampai", text="Estimasi Sampai")
        paket_tree.heading("Map", text="Map URL")
        paket_tree.heading("Status", text="Status")
        paket_tree.heading("Kurir", text="Kurir")
        paket_tree.pack(pady=10)

        ttk.Label(paket_window, text="Perbarui Status Paket").pack(pady=5)
        status_combobox = ttk.Combobox(paket_window, values=["Menunggu konfirmasi", "Diterima", "Ditolak", "Dibatalkan"])
        status_combobox.pack(pady=5)
        ttk.Button(paket_window, text="Perbarui Status", command=update_status).pack(pady=10)

        ttk.Label(paket_window, text="Tetapkan Kurir").pack(pady=5)
        kurir_combobox = ttk.Combobox(paket_window, values=[kurir.nama for kurir in self.store.kurir_list], state="readonly")
        kurir_combobox.pack(pady=5)
        ttk.Button(paket_window, text="Tetapkan Kurir", command=assign_kurir).pack(pady=10)

        refresh_list()

    def show_user_menu(self):
        self.clear_window()

        ttk.Label(self.root, text="Menu Pengguna", font=("Helvetica", 16, "bold"), foreground="white").pack(pady=10)
        ttk.Button(self.root, text="Tambah Paket Baru", command=self.add_paket).pack(pady=5)
        ttk.Button(self.root, text="Kembali", command=self.show_main_menu).pack(pady=20)

    def add_paket(self):
        def submit_paket():
            pengirim = pengirim_entry.get()
            penerima = penerima_entry.get()
            asal = asal_entry.get()
            tujuan = tujuan_entry.get()
            panjang = panjang_entry.get()
            lebar = lebar_entry.get()
            tinggi = tinggi_entry.get()
            berat = berat_entry.get()
            pengiriman = jenis_pengiriman.get()

            if pengirim and penerima and asal and tujuan and panjang and lebar and tinggi and berat and pengiriman:
                try:
                    panjang = float(panjang)
                    lebar = float(lebar)
                    tinggi = float(tinggi)
                    berat = float(berat)
                    jarak, durasi, map_url = self.calculate_distance(asal, tujuan)

                    if jarak is not None and durasi is not None:
                        tanggal_penambahan = datetime.now()
                        ongkir = self.calculate_cost(jarak, panjang, lebar, berat, pengiriman)
                        estimasi_sampai = self.calculate_estimation(tanggal_penambahan, durasi, pengiriman)
                        paket = Paket(self.store.paket_id_counter, pengirim, penerima, asal, tujuan, panjang, lebar, tinggi, berat, jarak, pengiriman, ongkir, tanggal_penambahan, estimasi_sampai, map_url)
                        self.store.tambah_paket(paket)
                        self.store.paket_id_counter += 1
                        messagebox.showinfo("Sukses", f"Paket ID {paket.id} berhasil ditambahkan.")
                        paket_window.destroy()
                except ValueError:
                    messagebox.showerror("Error", "Semua dimensi dan berat harus berupa angka.")
            else:
                messagebox.showerror("Error", "Semua bidang harus diisi.")

        paket_window = tk.Toplevel(self.root)
        paket_window.title("Tambah Paket Baru")
        paket_window.configure(bg="#003166")

        ttk.Label(paket_window, text="Pengirim", background="#003166").pack(pady=5)
        pengirim_entry = ttk.Entry(paket_window)
        pengirim_entry.pack(pady=5)

        ttk.Label(paket_window, text="Penerima", background="#003166").pack(pady=5)
        penerima_entry = ttk.Entry(paket_window)
        penerima_entry.pack(pady=5)

        ttk.Label(paket_window, text="Asal", background="#003166").pack(pady=5)
        asal_entry = ttk.Entry(paket_window)
        asal_entry.pack(pady=5)

        ttk.Label(paket_window, text="Tujuan", background="#003166").pack(pady=5)
        tujuan_entry = ttk.Entry(paket_window)
        tujuan_entry.pack(pady=5)

        ttk.Label(paket_window, text="Panjang (cm)", background="#003166").pack(pady=5)
        panjang_entry = ttk.Entry(paket_window)
        panjang_entry.pack(pady=5)

        ttk.Label(paket_window, text="Lebar (cm)", background="#003166").pack(pady=5)
        lebar_entry = ttk.Entry(paket_window)
        lebar_entry.pack(pady=5)

        ttk.Label(paket_window, text="Tinggi (cm)", background="#003166").pack(pady=5)
        tinggi_entry = ttk.Entry(paket_window)
        tinggi_entry.pack(pady=5)

        ttk.Label(paket_window, text="Berat (kg)", background="#003166").pack(pady=5)
        berat_entry = ttk.Entry(paket_window)
        berat_entry.pack(pady=5)

        ttk.Label(paket_window, text="Jenis pengiriman", background="#003166").pack(pady=5)
        jenis_pengiriman = ttk.Combobox(paket_window, values=["Reguler", "Express"], width=18, state="readonly")
        jenis_pengiriman.pack(pady=5)

        ttk.Button(paket_window, text="Tambah", command=submit_paket).pack(pady=10)


    def calculate_distance(self, origin, destination):
        try:
            # Geocoding untuk mendapatkan koordinat asal dan tujuan
            loc_origin = self.geolocator.geocode(origin)
            loc_destination = self.geolocator.geocode(destination)

            if loc_origin and loc_destination:
                # Koordinat dalam format longitude,latitude
                coords_origin = (loc_origin.longitude, loc_origin.latitude)
                coords_destination = (loc_destination.longitude, loc_destination.latitude)
                map_url = self.open_map(coords_origin, coords_destination)

                # Format URL API OSRM
                coordinates = f"{coords_origin[0]},{coords_origin[1]};{coords_destination[0]},{coords_destination[1]}"
                url = f"{self.base_url}/route/v1/driving/{coordinates}"

                # Permintaan ke API OSRM
                response = requests.get(url, params={"overview": "false"})  # Nonaktifkan geometri untuk efisiensi
                if response.status_code == 200:
                    data = response.json()
                    route = data["routes"][0] 

                    # Jarak dalam kilometer dan waktu dalam menit
                    jarak = route["distance"] / 1000  
                    durasi = route["duration"] / 60
                    return jarak, durasi, map_url
                else:
                    messagebox.showerror("Error", f"OSRM API Error: {response.status_code} {response.text}")
                    return None, None, None
            else:
                messagebox.showerror("Error", "Alamat tidak ditemukan.")
                return None, None, None
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menghitung jarak: {e}")
            return None, None, None
    
    def calculate_cost(self, jarak, panjang, lebar, berat, pengiriman):
        discount = 1.0
        if(pengiriman == "Reguler"):
            discount = 0.7
        ongkir_jarak = jarak * 2000 * discount
        ongkir_dimensi = (panjang + lebar + berat) * 100
        ongkir = ongkir_jarak + ongkir_dimensi
        return ongkir
        
        
    def calculate_estimation(self, tanggal_penambahan, durasi, pengiriman):
        jam = 24
        if(pengiriman == "Express"):
            jam = 6
        total_waktu_pengiriman = durasi + jam * 60
        estimasi = tanggal_penambahan + timedelta(minutes=total_waktu_pengiriman)
        return estimasi
    
    
    def open_map(self, origin_coords, destination_coords):
        origin = f"{origin_coords[1]},{origin_coords[0]}"
        destination = f"{destination_coords[1]},{destination_coords[0]}"
        url = f"https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route={origin};{destination}"
        webbrowser.open(url)
        return url

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PengirimanPaketApp(root)
    root.mainloop()
