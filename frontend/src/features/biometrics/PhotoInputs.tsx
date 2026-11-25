import { useEffect, useRef, type ChangeEvent } from "react";

export function supportedPhoto(file: File) {
  return (!file.type || ["image/jpeg", "image/png"].includes(file.type))
    && file.size > 0 && file.size <= 4 * 1024 * 1024;
}

export function toBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const data = typeof reader.result === "string" ? reader.result.split(",", 2)[1] : undefined;
      if (data) resolve(data);
      else reject(new Error("Foto inválida."));
    };
    reader.onerror = () => reject(new Error("Erro ao ler a foto."));
    reader.readAsDataURL(file);
  });
}

export function PhotoInputs({ onChange }: { onChange: (event: ChangeEvent<HTMLInputElement>) => void }) {
  return <>
    <label>Selecionar foto <input type="file" accept="image/jpeg,image/png" onChange={onChange} /></label>
    <label>Tirar foto no celular <input type="file" accept="image/*" capture="user" onChange={onChange} /></label>
  </>;
}

export function SelectedPhoto({ file }: { file: File }) {
  const preview = useRef<HTMLImageElement>(null);
  useEffect(() => {
    const image = preview.current;
    if (!image || typeof URL.createObjectURL !== "function") return;
    const url = URL.createObjectURL(file);
    image.src = url;
    return () => {
      image.removeAttribute("src");
      URL.revokeObjectURL(url);
    };
  }, [file]);
  return <figure className="face-preview">
    {typeof URL.createObjectURL === "function" && <img ref={preview} alt="Prévia da foto selecionada" />}
    <figcaption role="status">Foto selecionada para envio · {file.name}</figcaption>
  </figure>;
}
