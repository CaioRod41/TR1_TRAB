# src/camada_enlace/CamadaEnlace.py
class CamadaEnlace:
    # --------------------------------------INICIO DA 1.4-------------------------------------------------
    def encode_paridade(self, bits):
        count_ones = sum(bits)
        paridade = 0
        if (count_ones % 2 != 0):
            paridade = 1
        return bits + [paridade]

    def decode_paridade(self, bits):
        if len(bits) == 0:
            return bits, True

        payload = bits[:-1]
        bit_p = bits[-1]

        erro = ((sum(payload) + bit_p) % 2) != 0
        return payload, erro

    def encode_checksum(self, bits):
        """
        Implementa o checksum conforme a treliça fixa 000.
        Ao final, adiciona os 3 bits do checksum ao quadro.
        """
        estado = [0, 0, 0]

        for b in bits:
            # deslocamento (shift right): e2 = e1, e1 = e0, e0 = novo bit
            estado = [b, estado[0], estado[1]]

        # estado final é o checksum
        checksum = estado[:]  # copia

        # retorna quadro + checksum
        return bits + checksum

    def decode_checksum(self, bits):
        """
        Decodifica o checksum calculando novamente a treliça
        e comparando com o checksum anexado.
        Retorna (bits_sem_checksum, erro_detectado)
        """

        if len(bits) < 3:
            return bits, True

        # separa payload e checksum
        payload = bits[:-3]
        checksum_rx = bits[-3:]

        # recalcula checksum
        estado = [0, 0, 0]

        for b in payload:
            estado = [b, estado[0], estado[1]]

        checksum_calc = estado[:]

        erro = (checksum_calc != checksum_rx)

        return payload, erro

    def encode_crc(self, bits):
        """
        Implementação ACADÊMICA do CRC-32 real (Ethernet).
        Usa:
            - registrador 32 bits (treliça)
            - polinômio 0x04C11DB7
            - estado inicial 0xFFFFFFFF
            - reflexão implícita: NÃO usada aqui (versão simples)
            - XOR final 0xFFFFFFFF
        """
        poly = 0x04C11DB7
        reg = 0xFFFFFFFF  # treliça inicial (padrão CRC-32)

        for bit in bits:
            msb = (reg >> 31) & 1
            feedback = msb ^ bit

            reg = ((reg << 1) & 0xFFFFFFFF)

            if feedback == 1:
                reg ^= poly

        crc = reg ^ 0xFFFFFFFF  # XOR final

        crc_bits = [(crc >> (31 - i)) & 1 for i in range(32)]
        return bits + crc_bits

    def decode_crc(self, bits):
        """
        Verifica CRC-32 recomputando com a mesma lógica
        e comparando com o CRC recebido.
        """
        if len(bits) < 32:
            return bits, True

        payload = bits[:-32]
        crc_rx_bits = bits[-32:]

        crc_rx = 0
        for b in crc_rx_bits:
            crc_rx = (crc_rx << 1) | b

        poly = 0x04C11DB7
        reg = 0xFFFFFFFF

        for bit in payload:
            msb = (reg >> 31) & 1
            feedback = msb ^ bit

            reg = ((reg << 1) & 0xFFFFFFFF)

            if feedback == 1:
                reg ^= poly

        crc_calc = reg ^ 0xFFFFFFFF

        erro = (crc_calc != crc_rx)
        return payload, erro

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

# --------------------------------1.3 - ENQUADRAMENTO (Framing)-----------------------------------

      # --- 1. Contagem de Caracteres ---


    def enquadramento_contagem_caracteres(self, bits_dados):
        # Adiciona 1 byte de cabeçalho indicando o tamanho total (header + payload)
        bytes_dados = self._bits_to_bytes(bits_dados)
        quadro = []
        tamanho_max_payload = 255  # Limite de 1 byte

        # Cabeçalho indica o número de bytes no quadro (incluindo ele mesmo)
        count = len(bytes_dados) + 1
        quadro.append(count)
        quadro.extend(bytes_dados)

        return self._bytes_to_bits(quadro)


    def desenquadramento_contagem_caracteres(self, bits_quadro):
        bytes_quadro = self._bits_to_bytes(bits_quadro)
        if not bytes_quadro:
            return []

        # Lê o primeiro byte para saber o tamanho
        count = bytes_quadro[0]
        # Retorna apenas o payload (remove o count)
        return self._bytes_to_bits(bytes_quadro[1:count])

        # --- 2. Byte Stuffing (Inserção de Bytes) ---


    def enquadramento_flag_bytes(self, bits_dados):
        FLAG = 0x7E  # '~'
        ESC = 0x7D  # '}'

        bytes_dados = self._bits_to_bytes(bits_dados)
        quadro = [FLAG]

        for b in bytes_dados:
            if b == FLAG or b == ESC:
                quadro.append(ESC)
                quadro.append(b)
            else:
                quadro.append(b)

        quadro.append(FLAG)
        return self._bytes_to_bits(quadro)


    def desenquadramento_flag_bytes(self, bits_quadro):
        FLAG = 0x7E
        ESC = 0x7D
        bytes_quadro = self._bits_to_bytes(bits_quadro)
        dados = []

        ignore_next = False
        payload = bytes_quadro[1:-1]

        i = 0
        while i < len(payload):
            b = payload[i]
            if b == ESC:
                i += 1
                if i < len(payload):
                    dados.append(payload[i])
            else:
                dados.append(b)
            i += 1

        return self._bytes_to_bits(dados)

        # --- 3. Bit Stuffing (Inserção de Bits) ---


    def enquadramento_flag_bits(self, bits_dados):
        # Flag: 01111110. Regra: Se aparecerem 5 '1's seguidos nos dados, insere um '0'.
        saida = []
        conta_um = 0

        # Adiciona Flag de início
        flag = [0, 1, 1, 1, 1, 1, 1, 0]
        saida.extend(flag)

        for b in bits_dados:
            saida.append(b)
            if b == 1:
                conta_um += 1
                if conta_um == 5:
                    saida.append(0)  # Stuffing
                    conta_um = 0
            else:
                conta_um = 0

        # Adiciona Flag de fim
        saida.extend(flag)
        return saida


    def desenquadramento_flag_bits(self, bits_quadro):
        # Remove Flags (assumindo 8 bits no inicio e fim)
        payload = bits_quadro[8:-8]
        saida = []
        conta_um = 0

        i = 0
        while i < len(payload):
            b = payload[i]
            saida.append(b)

            if b == 1:
                conta_um += 1
                if conta_um == 5:
                    # O próximo bit deve ser o '0' de stuffing, pulamos ele
                    if i + 1 < len(payload) and payload[i + 1] == 0:
                        i += 1  # Pula o 0 inserido
                    conta_um = 0
            else:
                conta_um = 0
            i += 1

        return saida

        # --- Helpers Auxiliares ---


    def _bits_to_bytes(self, bits):
        # Converte array de bits para lista de inteiros (bytes)
        # (Você pode copiar a lógica do CamadaFisica.bytes_from_bits)
        pad = (-len(bits)) % 8
        bits = bits + [0] * pad
        out = []
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                byte = (byte << 1) | bits[i + j]
            out.append(byte)
        return out


    def _bytes_to_bits(self, bytes_list):
        bits = []
        for b in bytes_list:
            for i in range(8):
                bits.append((b >> (7 - i)) & 1)
        return bits