# src/camada_enlace/CamadaEnlace.py
class CamadaEnlace:
  #--------------------------------------INICIO DA 1.5-------------------------------------------------
    def hamming_encode(self, bits):
       
        encoded = []

        # padding para múltiplo de 4
        pad = (-len(bits)) % 4
        bits = bits + [0] * pad

        for i in range(0, len(bits), 4):
            d1, d2, d3, d4 = bits[i:i+4]

            # paridades
            p1 = d1 ^ d2 ^ d4
            p2 = d1 ^ d3 ^ d4
            p3 = d2 ^ d3 ^ d4

            # ordem final (7 bits)
            block = [p1, p2, d1, p3, d2, d3, d4]
            encoded.extend(block)

        return encoded

    # -------------------------------------
    # DECODER
    # -------------------------------------
    def hamming_decode(self, bits):
        """
        Decodifica blocos de 7 bits, corrige 1 erro,
        retorna lista de bits de dados (4 bits por bloco).
        """
        decoded = []

        # certifica que temos múltiplo de 7
        if len(bits) % 7 != 0:
            bits = bits[: len(bits) - (len(bits) % 7)]

        for i in range(0, len(bits), 7):
            block = bits[i:i+7]
            p1, p2, d1, p3, d2, d3, d4 = block

            # calcula sindromes
            s1 = p1 ^ d1 ^ d2 ^ d4
            s2 = p2 ^ d1 ^ d3 ^ d4
            s3 = p3 ^ d2 ^ d3 ^ d4

            # converte síndrome para posição do erro (1-7)
            error_pos = s1 + (s2 << 1) + (s3 << 2)

            # corrige
            if error_pos != 0:
                block[error_pos - 1] ^= 1  # inverte bit

                # reatribui
                p1, p2, d1, p3, d2, d3, d4 = block

            decoded.extend([d1, d2, d3, d4])

        return decoded
#--------------------------------------FIM DA 1.5-------------------------------------------------