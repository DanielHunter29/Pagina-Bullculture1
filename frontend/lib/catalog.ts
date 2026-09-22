/** Opciones de filtro y orden del catálogo (reflejan las choices del backend). */

export const GOALS = [
  { value: "ganar_masa", label: "Ganar masa muscular" },
  { value: "fuerza", label: "Fuerza" },
  { value: "definicion", label: "Definición" },
  { value: "energia", label: "Energía / pre-entreno" },
  { value: "recuperacion", label: "Recuperación" },
  { value: "salud", label: "Salud y bienestar" },
  { value: "perdida_peso", label: "Pérdida de peso" },
] as const;

export const ORDERINGS = [
  { value: "-created_at", label: "Más recientes" },
  { value: "price", label: "Precio: menor a mayor" },
  { value: "-price", label: "Precio: mayor a menor" },
  { value: "name", label: "Nombre: A → Z" },
] as const;

export const PAGE_SIZE = 12;
