const timeZone = "America/Sao_Paulo";
const localFormatter = new Intl.DateTimeFormat("sv-SE", {
  timeZone, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
});
const offsetFormatter = new Intl.DateTimeFormat("en-US", { timeZone, timeZoneName: "longOffset" });

export const scheduleTime = new Intl.DateTimeFormat("pt-BR", {
  timeZone, dateStyle: "short", timeStyle: "short",
});

export function academyLocalTime(value: string | number) {
  return localFormatter.format(new Date(value)).replace(" ", "T");
}

export function academyIsoTime(date: string, time: string, original?: string) {
  const local = date + "T" + time;
  if (original && academyLocalTime(original) === local) return original;
  const probe = Date.parse(local + "Z");
  if (!Number.isFinite(probe)) return null;

  const day = 24 * 60 * 60 * 1000;
  const offsets = new Set([probe - day, probe, probe + day].map(instant =>
    offsetFormatter.formatToParts(instant).find(part => part.type === "timeZoneName")?.value.slice(3) || "+00:00",
  ));
  const matches = [...offsets].map(offset => Date.parse(local + offset)).filter(
    instant => Number.isFinite(instant) && academyLocalTime(instant) === local,
  );
  // Horas inexistentes ou ambíguas em transições de fuso exigem outro horário local.
  return matches.length === 1 ? new Date(matches[0]).toISOString() : null;
}
