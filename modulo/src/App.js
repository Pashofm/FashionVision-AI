import React, { useState, useRef, useEffect } from "react";
import * as mobilenet from "@tensorflow-models/mobilenet";
import "@tensorflow/tfjs";

function App() {
  const [productos, setProductos] = useState([]);
  const [mostrarModal, setMostrarModal] = useState(false);

  const [nombre, setNombre] = useState("");
  const [cantidad, setCantidad] = useState("");
  const [precio, setPrecio] = useState("");

  const [imagen, setImagen] = useState(null);
  const [color, setColor] = useState("");
  const [tipoPrenda, setTipoPrenda] = useState("");

  const [stream, setStream] = useState(null);
  const [model, setModel] = useState(null);
  const [modeloListo, setModeloListo] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // ✅ Cargar modelo IA
  useEffect(() => {
    const cargarModelo = async () => {
      try {
        const modelo = await mobilenet.load();
        setModel(modelo);
        setModeloListo(true);
        console.log("Modelo cargado correctamente");
      } catch (error) {
        console.error("Error cargando modelo:", error);
      }
    };

    cargarModelo();
  }, []);

  // ✅ Abrir cámara
  const abrirCamara = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: true
      });

      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (error) {
      alert("No se pudo acceder a la cámara");
    }
  };

  // Detectar color dominante
  const detectarColor = (canvas) => {
    const ctx = canvas.getContext("2d");
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;

    let r = 0, g = 0, b = 0;
    let total = data.length / 4;

    for (let i = 0; i < data.length; i += 4) {
      r += data[i];
      g += data[i + 1];
      b += data[i + 2];
    }

    r = Math.floor(r / total);
    g = Math.floor(g / total);
    b = Math.floor(b / total);

    if (r > g && r > b) return "Rojo";
    if (g > r && g > b) return "Verde";
    if (b > r && b > g) return "Azul";
    if (r > 200 && g > 200 && b > 200) return "Blanco";
    if (r < 50 && g < 50 && b < 50) return "Negro";

    return "Color mixto";
  };

  // ✅ Traducir categorías
  const traducirCategoria = (texto) => {
    const t = texto.toLowerCase();
    if (t.includes("t-shirt")) return "Playera";
    if (t.includes("shirt")) return "Camisa";
    if (t.includes("jacket")) return "Chaqueta";
    if (t.includes("jean")) return "Pantalón";
    if (t.includes("dress")) return "Vestido";
    return texto;
  };

  // Tomar foto + IA (CORREGIDO)
  const tomarFoto = async () => {
    const canvas = canvasRef.current;
    const video = videoRef.current;

    if (!video || !canvas) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0);

    const imagenCapturada = canvas.toDataURL("image/png");
    setImagen(imagenCapturada);

    // Detectar color
    const colorDetectado = detectarColor(canvas);
    setColor(colorDetectado);

    if (!model) {
      console.log("Modelo aún no cargado");
      return;
    }

    try {
      const imgElement = new Image();
      imgElement.src = imagenCapturada;

      await imgElement.decode();

      const predictions = await model.classify(imgElement);
      console.log("Predicciones:", predictions);

      if (predictions.length > 0) {
        const categoriaTraducida = traducirCategoria(predictions[0].className);
        setTipoPrenda(categoriaTraducida);
      }
    } catch (error) {
      console.error("Error clasificando:", error);
    }

    // Detener cámara
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
  };

  const agregarProducto = () => {
    if (!nombre || !cantidad || !precio) {
      alert("Nombre, cantidad y precio son obligatorios");
      return;
    }

    const nuevoProducto = {
      id: Date.now(),
      nombre,
      cantidad,
      precio,
      color,
      tipoPrenda,
      imagen
    };

    setProductos([...productos, nuevoProducto]);

    setNombre("");
    setCantidad("");
    setPrecio("");
    setImagen(null);
    setColor("");
    setTipoPrenda("");
    setMostrarModal(false);
  };

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <h1>Módulo de Inventario</h1>
        <button onClick={() => setMostrarModal(true)} style={btnAgregar}>
          + Agregar Producto
        </button>
      </div>

      <table border="1" cellPadding="10" style={{ marginTop: "20px", width: "100%" }}>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Cantidad</th>
            <th>Precio</th>
            <th>Color</th>
            <th>Tipo</th>
          </tr>
        </thead>
        <tbody>
          {productos.length === 0 ? (
            <tr>
              <td colSpan="5" align="center">No hay productos</td>
            </tr>
          ) : (
            productos.map((p) => (
              <tr key={p.id}>
                <td>{p.nombre}</td>
                <td>{p.cantidad}</td>
                <td>${p.precio}</td>
                <td>{p.color}</td>
                <td>{p.tipoPrenda}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      {mostrarModal && (
        <div style={overlayStyle}>
          <div style={modalStyle}>
            <h2>Agregar Producto</h2>

            <input type="text" placeholder="Nombre"
              value={nombre} onChange={(e) => setNombre(e.target.value)} style={inputStyle} />

            <input type="number" placeholder="Cantidad"
              value={cantidad} onChange={(e) => setCantidad(e.target.value)} style={inputStyle} />

            <input type="number" placeholder="Precio"
              value={precio} onChange={(e) => setPrecio(e.target.value)} style={inputStyle} />

            <button onClick={abrirCamara} style={{ marginBottom: "10px" }}>
              Abrir Cámara
            </button>

            <video ref={videoRef} autoPlay style={{ width: "100%", marginBottom: "10px" }} />

            <button 
              onClick={tomarFoto} 
              disabled={!modeloListo}
              style={{ marginBottom: "10px" }}
            >
              Tomar Foto
            </button>

            <canvas ref={canvasRef} style={{ display: "none" }} />

            {imagen && (
              <img src={imagen} alt="capturada"
                style={{ width: "100%", marginBottom: "10px" }} />
            )}

            <input type="text" value={color}
              placeholder="Color detectado"
              disabled style={inputDisabled} />

            <input type="text" value={tipoPrenda}
              placeholder="Tipo detectado"
              disabled style={inputDisabled} />

            <div style={{ marginTop: "15px", textAlign: "right" }}>
              <button onClick={() => setMostrarModal(false)} style={cancelBtn}>
                Cancelar
              </button>
              <button onClick={agregarProducto} style={saveBtn}>
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ESTILOS */

const btnAgregar = {
  padding: "10px 15px",
  backgroundColor: "#007bff",
  color: "white",
  border: "none",
  borderRadius: "5px",
  cursor: "pointer"
};

const overlayStyle = {
  position: "fixed",
  top: 0,
  left: 0,
  width: "100%",
  height: "100%",
  backgroundColor: "rgba(0,0,0,0.5)",
  display: "flex",
  justifyContent: "center",
  alignItems: "center"
};

const modalStyle = {
  backgroundColor: "white",
  padding: "30px",
  borderRadius: "10px",
  width: "450px",
  display: "flex",
  flexDirection: "column",
  maxHeight: "90vh",
  overflowY: "auto"
};

const inputStyle = {
  marginBottom: "10px",
  padding: "8px"
};

const inputDisabled = {
  marginBottom: "10px",
  padding: "8px",
  backgroundColor: "#f0f0f0",
  color: "#777"
};

const cancelBtn = {
  marginRight: "10px",
  padding: "8px 12px"
};

const saveBtn = {
  padding: "8px 12px",
  backgroundColor: "#28a745",
  color: "white",
  border: "none",
  cursor: "pointer"
};

export default App;