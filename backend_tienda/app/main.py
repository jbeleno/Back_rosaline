from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from . import models, schemas, crud
from .database import SessionLocal, engine
from .auth import crear_token_de_acceso, get_current_user, verify_password

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # O ["*"] solo para pruebas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Usuarios
@app.post("/usuarios/", response_model=schemas.Usuario)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    db_usuario = crud.get_usuario_por_correo(db, correo=usuario.correo)
    if db_usuario:
        raise HTTPException(status_code=400, detail="Correo ya registrado")
    return crud.crear_usuario(db=db, usuario=usuario)

# Clientes
@app.post("/clientes/", response_model=schemas.Cliente)
def crear_cliente(cliente: schemas.ClienteCreate, db: Session = Depends(get_db)):
    return crud.crear_cliente(db=db, cliente=cliente)

@app.get("/clientes/", response_model=list[schemas.Cliente])
def listar_clientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_clientes(db, skip=skip, limit=limit)

@app.get("/clientes/usuario/{id_usuario}", response_model=schemas.Cliente)
def obtener_cliente_por_usuario(id_usuario: int, db: Session = Depends(get_db)):
    cliente = crud.get_cliente_por_id_usuario(db, id_usuario)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

# Categorías
@app.post("/categorias/", response_model=schemas.Categoria)
def crear_categoria(categoria: schemas.CategoriaCreate, db: Session = Depends(get_db)):
    return crud.crear_categoria(db=db, categoria=categoria)

@app.get("/categorias/", response_model=list[schemas.Categoria])
def listar_categorias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_categorias(db, skip=skip, limit=limit)

# Productos
@app.post("/productos/", response_model=schemas.Producto)
def crear_producto(producto: schemas.ProductoCreate, db: Session = Depends(get_db)):
    return crud.crear_producto(db=db, producto=producto)

@app.get("/productos/", response_model=list[schemas.Producto])
def listar_productos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_productos(db, skip=skip, limit=limit)

# Pedidos
@app.post("/pedidos/", response_model=schemas.Pedido)
def crear_pedido(pedido: schemas.PedidoCreate, db: Session = Depends(get_db)):
    return crud.crear_pedido(db=db, pedido=pedido)

@app.get("/pedidos/", response_model=list[schemas.Pedido])
def listar_pedidos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_pedidos(db, skip=skip, limit=limit)

# Detalle de pedidos
@app.post("/detalle_pedidos/", response_model=schemas.DetallePedido)
def crear_detalle_pedido(detalle: schemas.DetallePedidoCreate, db: Session = Depends(get_db)):
    return crud.crear_detalle_pedido(db=db, detalle=detalle)

@app.get("/detalle_pedidos/", response_model=list[schemas.DetallePedido])
def listar_detalles_pedido(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_detalles_pedido(db, skip=skip, limit=limit)

# Usuarios - Editar y Eliminar
@app.put("/usuarios/{usuario_id}", response_model=schemas.Usuario)
def actualizar_usuario(usuario_id: int, usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    db_usuario = crud.actualizar_usuario(db, usuario_id, usuario)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario

@app.delete("/usuarios/{usuario_id}", response_model=schemas.Usuario)
def eliminar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    db_usuario = crud.eliminar_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario

# Clientes - Editar y Eliminar
@app.put("/clientes/{cliente_id}", response_model=schemas.Cliente)
def actualizar_cliente(cliente_id: int, cliente: schemas.ClienteCreate, db: Session = Depends(get_db)):
    db_cliente = crud.actualizar_cliente(db, cliente_id, cliente)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return db_cliente

@app.delete("/clientes/{cliente_id}", response_model=schemas.Cliente)
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    db_cliente = crud.eliminar_cliente(db, cliente_id)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return db_cliente

# Categorías - Editar y Eliminar
@app.put("/categorias/{categoria_id}", response_model=schemas.Categoria)
def actualizar_categoria(categoria_id: int, categoria: schemas.CategoriaCreate, db: Session = Depends(get_db)):
    db_categoria = crud.actualizar_categoria(db, categoria_id, categoria)
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return db_categoria

@app.delete("/categorias/{categoria_id}", response_model=schemas.Categoria)
def eliminar_categoria(categoria_id: int, db: Session = Depends(get_db)):
    db_categoria = crud.eliminar_categoria(db, categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return db_categoria

# Productos - Editar y Eliminar
@app.put("/productos/{producto_id}", response_model=schemas.Producto)
def actualizar_producto(producto_id: int, producto: schemas.ProductoCreate, db: Session = Depends(get_db)):
    db_producto = crud.actualizar_producto(db, producto_id, producto)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return db_producto

@app.delete("/productos/{id}")
def eliminar_producto(id: int, db: Session = Depends(get_db)):
    db_producto = crud.eliminar_producto(db, id)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"mensaje": "Producto eliminado correctamente"}

# Pedidos - Editar y Eliminar
@app.put("/pedidos/{pedido_id}", response_model=schemas.Pedido)
def actualizar_pedido(pedido_id: int, pedido: schemas.PedidoCreate, db: Session = Depends(get_db)):
    db_pedido = crud.actualizar_pedido(db, pedido_id, pedido)
    if not db_pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return db_pedido

@app.delete("/pedidos/{pedido_id}", response_model=schemas.Pedido)
def eliminar_pedido(pedido_id: int, db: Session = Depends(get_db)):
    db_pedido = crud.eliminar_pedido(db, pedido_id)
    if not db_pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return db_pedido

# Detalle de pedidos - Editar y Eliminar
@app.put("/detalle_pedidos/{detalle_id}", response_model=schemas.DetallePedido)
def actualizar_detalle_pedido(detalle_id: int, detalle: schemas.DetallePedidoCreate, db: Session = Depends(get_db)):
    db_detalle = crud.actualizar_detalle_pedido(db, detalle_id, detalle)
    if not db_detalle:
        raise HTTPException(status_code=404, detail="Detalle de pedido no encontrado")
    return db_detalle

@app.delete("/detalle_pedidos/{detalle_id}", response_model=schemas.DetallePedido)
def eliminar_detalle_pedido(detalle_id: int, db: Session = Depends(get_db)):
    db_detalle = crud.eliminar_detalle_pedido(db, detalle_id)
    if not db_detalle:
        raise HTTPException(status_code=404, detail="Detalle de pedido no encontrado")
    return db_detalle

# Buscar productos de un pedido
@app.get("/pedidos/{pedido_id}/productos", response_model=list[schemas.Producto])
def productos_de_pedido(pedido_id: int, db: Session = Depends(get_db)):
    detalles = db.query(models.DetallePedido).filter(models.DetallePedido.id_pedido == pedido_id).all()
    productos = [db.query(models.Producto).filter(models.Producto.id_producto == d.id_producto).first() for d in detalles]
    return productos

# Buscar productos de una categoría
@app.get("/categorias/{categoria_id}/productos", response_model=list[schemas.Producto])
def productos_de_categoria(categoria_id: int, db: Session = Depends(get_db)):
    return db.query(models.Producto).filter(models.Producto.id_categoria == categoria_id).all()

# Buscar pedidos de un cliente
@app.get("/clientes/{cliente_id}/pedidos", response_model=list[schemas.Pedido])
def pedidos_de_cliente(cliente_id: int, db: Session = Depends(get_db)):
    return db.query(models.Pedido).filter(models.Pedido.id_cliente == cliente_id).all()

# Listar pedidos por estado
@app.get("/pedidos/estado/{estado}", response_model=list[schemas.Pedido])
def listar_pedidos_por_estado(estado: str, db: Session = Depends(get_db)):
    return db.query(models.Pedido).filter(models.Pedido.estado == estado).all()

# Carrito
@app.post("/carritos/", response_model=schemas.Carrito)
def crear_carrito(carrito: schemas.CarritoCreate, db: Session = Depends(get_db)):
    return crud.crear_carrito(db=db, carrito=carrito)

@app.get("/carritos/", response_model=list[schemas.Carrito])
def listar_carritos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_carritos(db, skip=skip, limit=limit)

@app.put("/carritos/{carrito_id}", response_model=schemas.Carrito)
def actualizar_carrito(carrito_id: int, carrito: schemas.CarritoCreate, db: Session = Depends(get_db)):
    db_carrito = crud.actualizar_carrito(db, carrito_id, carrito)
    if not db_carrito:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")
    return db_carrito

@app.delete("/carritos/{carrito_id}", response_model=schemas.Carrito)
def eliminar_carrito(carrito_id: int, db: Session = Depends(get_db)):
    db_carrito = crud.eliminar_carrito(db, carrito_id)
    if not db_carrito:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")
    return db_carrito

# Detalle Carrito
@app.post("/detalle_carrito/", response_model=schemas.DetalleCarrito)
def crear_detalle_carrito(detalle: schemas.DetalleCarritoCreate, db: Session = Depends(get_db)):
    return crud.crear_detalle_carrito(db=db, detalle=detalle)

@app.get("/detalle_carrito/", response_model=list[schemas.DetalleCarrito])
def listar_detalles_carrito(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_detalles_carrito(db, skip=skip, limit=limit)

@app.put("/detalle_carrito/{detalle_id}", response_model=schemas.DetalleCarrito)
def actualizar_detalle_carrito(detalle_id: int, detalle: schemas.DetalleCarritoCreate, db: Session = Depends(get_db)):
    db_detalle = crud.actualizar_detalle_carrito(db, detalle_id, detalle)
    if not db_detalle:
        raise HTTPException(status_code=404, detail="Detalle de carrito no encontrado")
    return db_detalle

@app.delete("/detalle_carrito/{detalle_id}")
def eliminar_detalle_carrito(detalle_id: int, db: Session = Depends(get_db)):
    db_detalle = crud.eliminar_detalle_carrito(db, detalle_id)
    if not db_detalle:
        raise HTTPException(status_code=404, detail="Detalle de carrito no encontrado")
    return {"mensaje": "Eliminado correctamente"}

# Carritos de un cliente
@app.get("/clientes/{cliente_id}/carritos", response_model=list[schemas.Carrito])
def carritos_de_cliente(cliente_id: int, db: Session = Depends(get_db)):
    return db.query(models.Carrito).filter(models.Carrito.id_cliente == cliente_id).all()

# Productos de un carrito
@app.get("/carritos/{carrito_id}/productos", response_model=list[schemas.Producto])
def productos_de_carrito(carrito_id: int, db: Session = Depends(get_db)):
    detalles = db.query(models.DetalleCarrito).filter(models.DetalleCarrito.id_carrito == carrito_id).all()
    productos = [db.query(models.Producto).filter(models.Producto.id_producto == d.id_producto).first() for d in detalles]
    return productos

@app.post("/login")
def login(datos: dict = Body(...), db: Session = Depends(get_db)):
    correo = datos.get("correo")
    contraseña = datos.get("contraseña")
    usuario = crud.get_usuario_por_correo(db, correo=correo)
    if not usuario or not verify_password(contraseña, usuario.contraseña):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    # Crear el token
    token = crear_token_de_acceso({"sub": usuario.correo, "id_usuario": usuario.id_usuario, "rol": usuario.rol})
    return {
        "access_token": token,
        "token_type": "bearer"
    }

@app.get("/usuarios/me")
def leer_usuarios_me(current_user: dict = Depends(get_current_user)):
    return current_user
