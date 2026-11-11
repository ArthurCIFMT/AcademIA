import json
import sys
from contextlib import redirect_stdout


def main() -> None:
    model = None
    for line in sys.stdin.buffer:
        try:
            request = json.loads(line)
            if model is None:
                with redirect_stdout(sys.stderr):
                    import torch
                    from sentence_transformers import SentenceTransformer

                    torch.set_num_threads(request["threads"])
                    model = SentenceTransformer(
                        request["path"],
                        device="cpu",
                        local_files_only=True,
                        trust_remote_code=False,
                        model_kwargs={"use_safetensors": True},
                    )
                if (
                    model.get_sentence_embedding_dimension() != 384
                    or model.max_seq_length != 512
                ):
                    raise ValueError("Espaço incompatível.")
            vectors = model.encode(
                request["texts"],
                batch_size=len(request["texts"]),
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
            result = {"status": "OK", "vectors": vectors.tolist()}
        except Exception:
            result = {"status": "ERRO", "code": "SERVICO_INDISPONIVEL"}
        sys.stdout.buffer.write(json.dumps(result).encode() + b"\n")
        sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
