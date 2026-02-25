import tkinter as tk
from tkinter import ttk

# Función para abrir ventanas
def abrir_ventana(titulo):
    root.withdraw()  # Oculta ventana principal
    
    ventana = tk.Toplevel()
    ventana.title(titulo)
    ventana.geometry("300x200")

    # Cuando se cierre con la X
    def cerrar():
        ventana.destroy()
        root.deiconify()  # Muestra nuevamente el menú principal

    ventana.protocol("WM_DELETE_WINDOW", cerrar)

    tk.Label(ventana, text=f"Ventana de {titulo}", 
             font=("Arial", 14)).pack(pady=30)

    ttk.Button(ventana, text="Cerrar", command=cerrar).pack(pady=10)

# Ventana principal
root = tk.Tk()
root.title("Menú Principal")
root.geometry("400x400")
root.configure(bg="#f2f2f2")

# Cuadro del título
frame_titulo = tk.Frame(root, bg="black", padx=10, pady=10)
frame_titulo.pack(pady=30)

titulo = tk.Label(frame_titulo, text="FashionVisionIA",
                  font=("Arial", 20, "bold"),
                  fg="white", bg="black")
titulo.pack()

# Botones
ttk.Button(root, text="Inventario",
           command=lambda: abrir_ventana("Inventario")
           ).pack(pady=10, ipadx=20, ipady=5)

ttk.Button(root, text="Cobro",
           command=lambda: abrir_ventana("Cobro")
           ).pack(pady=10, ipadx=20, ipady=5)

ttk.Button(root, text="Ventas",
           command=lambda: abrir_ventana("Ventas")
           ).pack(pady=10, ipadx=20, ipady=5)

root.mainloop()
