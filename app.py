from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'biblioteca.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.executescript('''
    CREATE TABLE IF NOT EXISTS autores (
        id_autor INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        anio TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS categorias (
        id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS libros (
        id_libro INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        id_autor INTEGER NOT NULL,
        id_categoria INTEGER NOT NULL,
        anio_publicacion INTEGER NOT NULL,
        FOREIGN KEY (id_autor) REFERENCES autores (id_autor),
        FOREIGN KEY (id_categoria) REFERENCES categorias (id_categoria)
    );

    CREATE TABLE IF NOT EXISTS prestamos (
        id_prestamos INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_prestamo TEXT NOT NULL,
        fecha_devolucion TEXT,
        id_libro INTEGER NOT NULL,
        FOREIGN KEY (id_libro) REFERENCES libros (id_libro)
    );
                             
    -- NUEVAS TABLAS PARA REUTILIZACIÓN DE IDs
    CREATE TABLE IF NOT EXISTS ids_libres_autores (
        id INTEGER PRIMARY KEY
    );
                             
    CREATE TABLE IF NOT EXISTS ids_libres_categorias (
        id INTEGER PRIMARY KEY
    );

    CREATE TABLE IF NOT EXISTS ids_libres_libros (
        id INTEGER PRIMARY KEY
    );
                             
    CREATE TABLE IF NOT EXISTS ids_libres_prestamos (
        id INTEGER PRIMARY KEY
    );
''')
        
        cursor.execute("INSERT INTO autores (id_autor, nombre, anio) VALUES (?, ?, ?)", (1, 'Gabriel García Márquez', '1927'))
        cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", ('Realismo Mágico',))
        id_categoria = cursor.lastrowid
        cursor.execute("INSERT INTO libros (id_libro, titulo, id_autor, id_categoria, anio_publicacion) VALUES (?, ?, ?, ?, ?)",
                       (1, 'Cien años de soledad', 1, id_categoria, 1967))
        conn.commit()
        conn.close()
        print("Base de datos creada con datos de prueba.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/libros')
def listar_libros():
    conn = get_db_connection()
    libros = conn.execute('''
        SELECT l.*, a.nombre AS autor, c.nombre AS categoria
        FROM libros l
        JOIN autores a ON l.id_autor = a.id_autor
        JOIN categorias c ON l.id_categoria = c.id_categoria
    ''').fetchall()
    conn.close()
    return render_template('libros.html', libros=libros)

@app.route('/agregar_libro', methods=['GET', 'POST'])
def agregar_libro():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        titulo = request.form['titulo']
        id_autor = request.form.get('id_autor')
        id_categoria = request.form.get('id_categoria')
        anio_publicacion = request.form['anio_publicacion']

        nuevo_autor = request.form.get('nuevo_autor')
        anio_autor = request.form.get('anio_autor')
        if nuevo_autor and anio_autor:
            id_autor_libre = cursor.execute('SELECT id FROM ids_libres_autores ORDER BY id LIMIT 1').fetchone()
            if id_autor_libre:
                id_autor = id_autor_libre['id']
                cursor.execute('DELETE FROM ids_libres_autores WHERE id = ?', (id_autor,))
                cursor.execute('INSERT INTO autores (id_autor, nombre, anio) VALUES (?, ?, ?)', (id_autor, nuevo_autor, anio_autor))
            else:
                cursor.execute('INSERT INTO autores (nombre, anio) VALUES (?, ?)', (nuevo_autor, anio_autor))
                id_autor = cursor.lastrowid

        nueva_categoria = request.form.get('nueva_categoria')
        if nueva_categoria:
            cursor.execute('INSERT INTO categorias (nombre) VALUES (?)', (nueva_categoria,))
            id_categoria = cursor.lastrowid

        id_libro_reutilizable = cursor.execute('SELECT id FROM ids_libres_libros ORDER BY id LIMIT 1').fetchone()
        if id_libro_reutilizable:
            id_libro = id_libro_reutilizable['id']
            cursor.execute('DELETE FROM ids_libres_libros WHERE id = ?', (id_libro,))
        else:
            id_libro = None

        cursor.execute('''
            INSERT INTO libros (id_libro, titulo, id_autor, id_categoria, anio_publicacion)
            VALUES (?, ?, ?, ?, ?)
        ''', (id_libro, titulo, id_autor, id_categoria, anio_publicacion))
        conn.commit()
        conn.close()
        return redirect(url_for('listar_libros'))

    autores = conn.execute('SELECT * FROM autores').fetchall()
    categorias = conn.execute('SELECT * FROM categorias').fetchall()
    conn.close()
    return render_template('agregar_libro.html', autores=autores, categorias=categorias)

@app.route('/eliminar_libro/<int:id>')
def eliminar_libro(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM libros WHERE id_libro = ?', (id,))
    conn.execute('INSERT INTO ids_libres_libros (id) VALUES (?)', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('listar_libros'))

@app.route('/editar_libro/<int:id>', methods=['GET', 'POST'])
def editar_libro(id):
    conn = get_db_connection()
    if request.method == 'POST':
        titulo = request.form['titulo']
        id_autor = request.form['id_autor']
        id_categoria = request.form['id_categoria']
        anio_publicacion = request.form['anio_publicacion']

        conn.execute('''
            UPDATE libros SET titulo = ?, id_autor = ?, id_categoria = ?, anio_publicacion = ?
            WHERE id_libro = ?
        ''', (titulo, id_autor, id_categoria, anio_publicacion, id))
        conn.commit()
        conn.close()
        return redirect(url_for('listar_libros'))

    libro = conn.execute('SELECT * FROM libros WHERE id_libro = ?', (id,)).fetchone()
    autores = conn.execute('SELECT * FROM autores').fetchall()
    categorias = conn.execute('SELECT * FROM categorias').fetchall()
    conn.close()
    return render_template('editar_libro.html', libro=libro, autores=autores, categorias=categorias)

@app.route('/autores', methods=['GET', 'POST'])
def listar_autores():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        nuevo_autor = request.form['nuevo_autor']
        anio_autor = request.form['anio_autor']

        id_libre = cursor.execute('SELECT id FROM ids_libres_autores ORDER BY id LIMIT 1').fetchone()
        if id_libre:
            autor_id = id_libre['id']
            cursor.execute('DELETE FROM ids_libres_autores WHERE id = ?', (autor_id,))
            cursor.execute('INSERT INTO autores (id_autor, nombre, anio) VALUES (?, ?, ?)',
                           (autor_id, nuevo_autor, anio_autor))
        else:
            cursor.execute('INSERT INTO autores (nombre, anio) VALUES (?, ?)',
                           (nuevo_autor, anio_autor))

        conn.commit()
        conn.close()
        return redirect(url_for('listar_autores'))

    autores = conn.execute('SELECT * FROM autores').fetchall()
    conn.close()
    return render_template('autores.html', autores=autores)

@app.route('/eliminar_autor/<int:id>')
def eliminar_autor(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM autores WHERE id_autor = ?', (id,))
    conn.execute('INSERT INTO ids_libres_autores (id) VALUES (?)', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('listar_autores'))

@app.route('/editar_autor/<int:id>', methods=['GET', 'POST'])
def editar_autor(id):
    conn = get_db_connection()
    autor = conn.execute('SELECT * FROM autores WHERE id_autor = ?', (id,)).fetchone()
    if request.method == 'POST':
        nuevo_nombre = request.form['nuevo_nombre']
        nuevo_anio = request.form['nuevo_anio']
        conn.execute('UPDATE autores SET nombre = ?, anio = ? WHERE id_autor = ?', (nuevo_nombre, nuevo_anio, id))
        conn.commit()
        conn.close()
        return redirect(url_for('listar_autores'))
    conn.close()
    return render_template('editar_autor.html', autor=autor)

@app.route('/categorias', methods=['GET', 'POST'])
def listar_categorias():
    conn = get_db_connection()
    if request.method == 'POST':
        nueva_categoria = request.form['nueva_categoria']
        conn.execute('INSERT INTO categorias (nombre) VALUES (?)', (nueva_categoria,))
        conn.commit()
        conn.close()
        return redirect(url_for('listar_categorias'))

    categorias = conn.execute('SELECT * FROM categorias').fetchall()
    conn.close()
    return render_template('categorias.html', categorias=categorias)

@app.route('/eliminar_categoria/<int:id>')
def eliminar_categoria(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM categorias WHERE id_categoria = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('listar_categorias'))

@app.route('/editar_categoria/<int:id>', methods=['GET', 'POST'])
def editar_categoria(id):
    conn = get_db_connection()
    categoria = conn.execute('SELECT * FROM categorias WHERE id_categoria = ?', (id,)).fetchone()
    if request.method == 'POST':
        nuevo_nombre = request.form['nuevo_nombre']
        conn.execute('UPDATE categorias SET nombre = ? WHERE id_categoria = ?', (nuevo_nombre, id))
        conn.commit()
        conn.close()
        return redirect(url_for('listar_categorias'))
    conn.close()
    return render_template('editar_categoria.html', categoria=categoria)

@app.route('/prestamos')
def listar_prestamos():
    conn = get_db_connection()
    prestamos = conn.execute('''
        SELECT p.id_prestamos, l.titulo AS libro, p.fecha_prestamo, p.fecha_devolucion
        FROM prestamos p
        JOIN libros l ON p.id_libro = l.id_libro
    ''').fetchall()
    conn.close()
    return render_template('prestamos.html', prestamos=prestamos)

@app.route('/agregar_prestamo', methods=['GET', 'POST'])
def agregar_prestamo():
    conn = get_db_connection()
    if request.method == 'POST':
        id_libro = request.form['id_libro']
        fecha_prestamo = request.form['id_fecha_prestamo']
        fecha_devolucion = request.form['id_fecha_devolucion']

        conn.execute('''
            INSERT INTO prestamos (id_libro, fecha_prestamo, fecha_devolucion)
            VALUES (?, ?, ?)
        ''', (id_libro, fecha_prestamo, fecha_devolucion))
        conn.commit()
        conn.close()
        return redirect(url_for('listar_prestamos'))

    libros = conn.execute('SELECT id_libro, titulo FROM libros').fetchall()
    conn.close()
    return render_template('agregar_prestamo.html', libros=libros)


@app.route('/editar_prestamo/<int:id>', methods=['GET', 'POST'])
def editar_prestamo(id):
    conn = get_db_connection()
    prestamos = conn.execute('SELECT * FROM prestamos WHERE id_prestamos = ?', (id,)).fetchone()

    if request.method == 'POST':
        id_libro = request.form['id_libro']
        fecha_prestamo = request.form['id_fecha_prestamo']
        fecha_devolucion = request.form['id_fecha_devolucion']

        conn.execute('''
            UPDATE prestamos
            SET id_libro = ?, fecha_prestamo = ?, fecha_devolucion = ?
            WHERE id_prestamos = ?
        ''', (id_libro, fecha_prestamo, fecha_devolucion, id))
        conn.commit()
        conn.close()
        return redirect(url_for('listar_prestamos'))

    libros = conn.execute('SELECT id_libro, titulo FROM libros').fetchall()
    conn.close()
    return render_template('editar_prestamo.html', prestamos=prestamos, libros=libros)

@app.route('/eliminar_prestamo/<int:id>')
def eliminar_prestamo(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM prestamos WHERE id_prestamos = ?', (id,))
    conn.execute('INSERT INTO ids_libres_prestamos (id) VALUES (?)', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('listar_prestamos'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
