from flask import Flask, request, render_template, redirect, url_for, flash
import sqlite3
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave_secreta_1234"

# Conexion y creacion de la base de datos socios.db
def get_db():
    conn = sqlite3.connect('socios.db')
    conn.row_factory = sqlite3.Row
    return conn

# Crear la tabla socios si no existe
with get_db() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS socios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            edad INTEGER NOT NULL,
            email TEXT NOT NULL,
            actividad TEXT NOT NULL
        )
    """)
    db.commit()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/agregar", methods=["GET", "POST"])
def agregar():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        edad_raw = request.form.get("edad", "").strip()
        email = request.form.get("email", "").strip()
        actividad = request.form.get("actividad", "").strip()

        errores = []
        if len(nombre) < 2:
            errores.append("El nombre debe tener al menos 2 caracteres.")
        if len(apellido) < 2:
            errores.append("El apellido debe tener al menos 2 caracteres.")
        if not edad_raw.isdigit():
            errores.append("La edad debe ser un número entero.")
        else:
            edad = int(edad_raw)
            if edad < 5 or edad > 120:
                errores.append("La edad está fuera del rango permitido.")
        if "@" not in email or len(email) < 5:
            errores.append("Ingrese un email válido.")
        if len(actividad) == 0:
            errores.append("Seleccione una actividad.")

        if errores:
            for e in errores:
                flash(e, "error")
            return redirect(url_for("agregar"))

        # Insertar en la base de datos
        with get_db() as db:
            db.execute(
                "INSERT INTO socios(nombre, apellido, edad, email, actividad) VALUES (?, ?, ?, ?, ?)",
                (nombre, apellido, edad, email, actividad)
            )
            db.commit()
        flash("Socio agregado correctamente.", "exito")
        return redirect(url_for("ver_socios"))

    # GET muestra el formulario
    actividades = ["Yoga", "Pilates", "Crossfit", "Spinning", "Natación", "Gimnasio"]
    return render_template("agregar.html", actividades=actividades)

@app.route("/ver")
def ver_socios():
    # Permitir buscar por nombre, apellido o actividad usando parámetros GET
    nombre_q = request.args.get("nombre", "").strip()
    apellido_q = request.args.get("apellido", "").strip()
    actividad_q = request.args.get("actividad", "").strip()

    db = get_db()
    query = "SELECT * FROM socios WHERE 1=1"
    params = []

    if nombre_q:
        query += " AND nombre LIKE ?"
        params.append(f"%{nombre_q}%")
    if apellido_q:
        query += " AND apellido LIKE ?"
        params.append(f"%{apellido_q}%")
    if actividad_q:
        query += " AND actividad = ?"
        params.append(actividad_q)

    socios = db.execute(query, params).fetchall()

    # Contadores para mensajes extras
    total = len(socios)
    return render_template("ver.html", socios=socios, total=total, filtros={
        "nombre": nombre_q,
        "apellido": apellido_q,
        "actividad": actividad_q
    })

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    db = get_db()
    socio = db.execute("SELECT * FROM socios WHERE id = ?", (id,)).fetchone()
    if not socio:
        flash("Socio no encontrado.", "error")
        return redirect(url_for("ver_socios"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        edad_raw = request.form.get("edad", "").strip()
        email = request.form.get("email", "").strip()
        actividad = request.form.get("actividad", "").strip()

        errores = []
        if len(nombre) < 2:
            errores.append("El nombre debe tener al menos 2 caracteres.")
        if len(apellido) < 2:
            errores.append("El apellido debe tener al menos 2 caracteres.")
        if not edad_raw.isdigit():
            errores.append("La edad debe ser un número entero.")
        else:
            edad = int(edad_raw)
            if edad < 5 or edad > 120:
                errores.append("La edad está fuera del rango permitido.")
        if "@" not in email or len(email) < 5:
            errores.append("Ingrese un email válido.")
        if len(actividad) == 0:
            errores.append("Seleccione una actividad.")

        if errores:
            for e in errores:
                flash(e, "error")
            return redirect(url_for("editar", id=id))

        db.execute(
            "UPDATE socios SET nombre=?, apellido=?, edad=?, email=?, actividad=? WHERE id=?",
            (nombre, apellido, edad, email, actividad, id)
        )
        db.commit()
        flash("Socio actualizado correctamente.", "exito")
        return redirect(url_for("ver_socios"))

    actividades = ["Yoga", "Pilates", "Crossfit", "Spinning", "Natación", "Gimnasio"]
    return render_template("editar.html", s=socio, actividades=actividades)

@app.route("/eliminar/<int:id>", methods=["GET", "POST"])
def eliminar(id):
    db = get_db()
    socio = db.execute("SELECT * FROM socios WHERE id = ?", (id,)).fetchone()
    if not socio:
        flash("Socio no encontrado.", "error")
        return redirect(url_for("ver_socios"))

    if request.method == "POST":
        db.execute("DELETE FROM socios WHERE id = ?", (id,))
        db.commit()
        flash("Socio eliminado.", "exito")
        return redirect(url_for("ver_socios"))

    return render_template("eliminar.html", s=socio)

@app.route("/export/csv")
def export_csv():
    db = get_db()
    socios = db.execute("SELECT * FROM socios").fetchall()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"socios_{timestamp}.csv"
    filepath = f"static/{filename}"

    # Escribimos el CSV en la carpeta static/
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "nombre", "apellido", "edad", "email", "actividad"])
        for s in socios:
            writer.writerow([s["id"], s["nombre"], s["apellido"], s["edad"], s["email"], s["actividad"]])

    flash(f"CSV generado: {filename}", "exito")
    return render_template("export.html", filepath=filename)

@app.route("/export/txt")
def export_txt():
    db = get_db()
    socios = db.execute("SELECT * FROM socios").fetchall()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"socios_{timestamp}.txt"
    filepath = f"static/{filename}"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("Listado de socios\n")
        f.write("=================\n")
        for s in socios:
            f.write(f"ID: {s['id']}\n")
            f.write(f"Nombre: {s['nombre']} {s['apellido']}\n")
            f.write(f"Edad: {s['edad']}\n")
            f.write(f"Email: {s['email']}\n")
            f.write(f"Actividad: {s['actividad']}\n")
            f.write("-----------------\n")

    flash(f"TXT generado: {filename}", "exito")
    return render_template("export.html", filepath=filename)

if __name__ == "__main__":
    app.run(debug=True)