const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export const money = (value: string) => currency.format(Number(value));
export const civilDate = (iso: string) => iso.split("-").reverse().join("/");
export const monthLabel = (iso: string) => civilDate(iso).slice(3);
