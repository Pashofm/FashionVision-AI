export const detectarColor = (canvas) => {
  const ctx = canvas.getContext('2d');
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

  if (r > g && r > b) return 'Rojo';
  if (g > r && g > b) return 'Verde';
  if (b > r && b > g) return 'Azul';
  if (r > 200 && g > 200 && b > 200) return 'Blanco';
  if (r < 50 && g < 50 && b < 50) return 'Negro';

  return 'Color mixto';
};

export const traducirCategoria = (texto) => {
  const traducciones = {
    't-shirt': 'Playera',
    'shirt': 'Camisa',
    'jacket': 'Chaqueta',
    'jean': 'Pantalón',
    'dress': 'Vestido',
    'shoe': 'Zapato',
    'sneaker': 'Zapatilla',
    'bag': 'Bolsa',
    'hat': 'Sombrero',
    'coat': 'Abrigo',
    'sweater': 'Suéter',
    'short': 'Short',
    'suit': 'Traje',
    'blazer': 'Blazer',
    'skirt': 'Falda',
    'hoodie': 'Sudadera con capucha',
    'cardigan': 'Cárdigan',
    'polo': 'Polo',
    'vest': 'Chaleco',
    'legging': 'Malla',
    'bikini': 'Bikini',
    'bra': 'Sujetador',
    'sock': 'Calcetines',
    'glove': 'Guante',
    'scarf': 'Bufanda',
    'belt': 'Cinturón',
    'watch': 'Reloj',
    'handbag': 'Bolso de mano',
    'wallet': 'Billetera',
    'backpack': 'Mochila',
    'briefcase': 'Maletín',
    'luggage': 'Equipaje',
    'gown': 'Bata',
    'maillot': 'Mayo',
    'poncho': 'Poncho',
    'stole': 'Estola',
    'cloak': 'Capa',
  };

  const t = texto.toLowerCase();
  
  for (const [key, value] of Object.entries(traducciones)) {
    if (t.includes(key)) {
      return value;
    }
  }
  
  return null;
};
