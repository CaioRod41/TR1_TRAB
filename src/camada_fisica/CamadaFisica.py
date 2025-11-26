import numpy as np

class CamadaFisica:
    """
    Cada método de codificação retorna (t, waveform) onde:
      - t: vetor de tempos (numpy array)
      - waveform: amostras (numpy array, float)
    Decodificadores retornam lista de bits (0/1).
    """

    def __init__(self, samples_per_bit=50, V=1.0, fs=None):
        """
        samples_per_bit: número de amostras por bit (inteiro)
        V: amplitude de pico
        fs: taxa de amostragem (opcional). Se None, fs = samples_per_bit / Tb (Tb=1s por bit nominal)
        """
        self.samples_per_bit = int(samples_per_bit)
        self.V = float(V)
        # se precisar usar tempo absoluto, assumimos Tb = 1.0 por símbolo para simplicidade
        self.Tb = 1.0
        self.fs = fs if fs is not None else self.samples_per_bit / self.Tb
        self.fc = 10.0 / self.Tb

        self.f1_fsk = 2.0 / self.Tb  # Frequência para bit '1' (ex: 2 Hz)
        self.f2_fsk = 1.0 / self.Tb  # Frequência para bit '0' (ex: 1 Hz)

        # -1 significa que o próximo '1' deve ser +1 (alterna de -1 para 1).
        self.last_polarity = -1 
        
    # -------------------------
    # Utilitários
    # -------------------------
    @staticmethod
    def bits_from_bytes(b: bytes):
        bits = []
        for byte in b:
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)
        return bits

    @staticmethod
    def bytes_from_bits(bits):
        # agrupa 8 bits MSB first
        pad = (-len(bits)) % 8
        bits = bits + [0] * pad
        out = bytearray()
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                byte = (byte << 1) | bits[i + j]
            out.append(byte)
        return bytes(out)

    # -------------------------
    # Função utilitária: adicionar ruído AWGN
    # -------------------------
    def add_awgn(self, waveform, snr_db):
        """
        Adiciona ruído AWGN ao waveform para um SNR (dB) fornecido.
        SNR definido como 10*log10(signal_power / noise_power).
        """
        sig_pow = np.mean(waveform ** 2)
        snr_linear = 10 ** (snr_db / 10.0)
        noise_pow = sig_pow / snr_linear if snr_linear != 0 else sig_pow * 0.001
        noise = np.sqrt(noise_pow) * np.random.randn(len(waveform))
        return waveform + noise

    def bits_to_symbols(self, bits, modulation='QPSK'):
        ''' Função para agrupar bits em síbolos (2 bits p/ QPSK e 4 bits p/ 16-QAM'''
        if modulation == 'QPSK':
            bits_per_symbol = 2
        else:
            bits_per_symbol = 4

        # Padding
        if len(bits) % bits_per_symbol != 0:
            pad = bits_per_symbol - (len(bits) % bits_per_symbol)
            bits = bits + [0] * pad

        simbolos = []
        for i in range(0, len(bits), bits_per_symbol):
            simbolo = tuple(bits[i:i + bits_per_symbol])
            simbolos.append(simbolo)

        return simbolos

    # -------------------------
    # 1.1.1 Modulção Digital
    # -------------------------
    """Implementa codificações banda-base digitais:
      - NRZ-Polar
      - Manchester
      - Bipolar (AMI)"""
    def nrz_polar(self, bits):
        """NRZ-Polar: 1 -> +V ; 0 -> -V"""
        s_per_bit = self.samples_per_bit
        waveform = np.zeros(len(bits) * s_per_bit, dtype=float)
        for i, b in enumerate(bits):
            level = self.V if b == 1 else -self.V
            waveform[i * s_per_bit : (i + 1) * s_per_bit] = level
        t = np.arange(len(waveform)) / self.fs
        return t, waveform

    def decode_nrz_polar(self, waveform):
        """Decodifica NRZ-Polar por média em cada intervalo de bit (threshold 0)."""
        s = self.samples_per_bit
        nb = len(waveform) // s
        bits = []
        for i in range(nb):
            chunk = waveform[i*s:(i+1)*s]
            m = np.mean(chunk)
            bits.append(1 if m > 0.0 else 0)
        return bits

    def manchester(self, bits):
        """Manchester:
           1 -> +V then -V
           0 -> -V then +V
        """
        s_per_bit = self.samples_per_bit
        half = s_per_bit // 2
     
        waveform = []
        for b in bits:
            if b == 1:
                waveform.extend([self.V] * half)
                waveform.extend([-self.V] * (s_per_bit - half))
            else:
                waveform.extend([-self.V] * half)
                waveform.extend([self.V] * (s_per_bit - half))
        waveform = np.array(waveform, dtype=float)
        t = np.arange(len(waveform)) / self.fs
        return t, waveform

    def decode_manchester(self, waveform):
        """Decodifica Manchester examinando as duas metades do bit."""
        s = self.samples_per_bit
        nb = len(waveform) // s
        bits = []
        half = s//2
        for i in range(nb):
            chunk = waveform[i*s:(i+1)*s]
            first_mean = np.mean(chunk[:half])
            second_mean = np.mean(chunk[half:])
            bits.append(1 if first_mean > second_mean else 0)
        return bits


    def bipolar_ami(self, bits):
        """
        Bipolar AMI:
           0 -> 0
           1 -> alterna +V / -V (primeiro 1 -> +V, próximo 1 -> -V, etc)
        """
        s_per_bit = self.samples_per_bit
        waveform = np.zeros(len(bits) * s_per_bit, dtype=float)
        
        last_polarity = -1
                          
      
        last_polarity = -1 # Assim o primeiro '1' é sempre +V.

        for i, b in enumerate(bits):
            if b == 0:
                level = 0.0
            else:
                # alternate polarity
                last_polarity *= -1 # -1 -> 1 (primeiro 1) ; 1 -> -1 (segundo 1)
                level = self.V * last_polarity
            waveform[i * s_per_bit : (i + 1) * s_per_bit] = level
            
        t = np.arange(len(waveform)) / self.fs
        return t, waveform

    def decode_bipolar_ami(self, waveform):
        """Decodifica AMI: decide 0 se média próxima de 0, senão 1."""
        s = self.samples_per_bit
        nb = len(waveform) // s
        bits = []
        for i in range(nb):
            chunk = waveform[i*s:(i+1)*s]
            m = np.mean(chunk)
            # threshold: se |m| < V/2 -> zero
            if abs(m) < (self.V * 0.4):
                bits.append(0)
            else:
                bits.append(1)
        return bits

    # -------------------------
    # 1.1.2 Modulação por Portadora
    # -------------------------
    def ask(self, bits):
        s_per_bit = self.samples_per_bit
        t_bit = np.arange(s_per_bit) / self.fs
        carrier = self.V * np.sin(2 * np.pi * self.fc * t_bit)

        waveform = np.array([], dtype=float)
        zero_signal = np.zeros(s_per_bit)

        for b in bits:
            if b == 1:
                waveform = np.append(waveform, carrier)
            else:
                waveform = np.append(waveform, zero_signal)

        t = np.arange(len(waveform)) / self.fs
        return t, waveform

    def decode_ask(self, waveform):
        s = self.samples_per_bit
        nb = len(waveform) // s
        threshold = (self.V ** 2) / 4.0  # Limiar baseado em 1/4 da potência
        bits = []
        for i in range(nb):
            chunk = waveform[i * s:(i + 1) * s]
            power = np.mean(chunk ** 2)
            bits.append(1 if power > threshold else 0)
        return bits

    def fsk(self, bits):
        """Modulação FSK, baseada na imagem (reinicia a fase a cada bit)"""
        s_per_bit = self.samples_per_bit
        t_bit = np.arange(s_per_bit) / self.fs

        # Pré-calcula a portadora para bit '1' (freq f1)
        carrier_1 = self.V * np.sin(2 * np.pi * self.f1_fsk * t_bit)

        # Pré-calcula a portadora para bit '0' (freq f2)
        carrier_0 = self.V * np.sin(2 * np.pi * self.f2_fsk * t_bit)

        waveform = np.array([], dtype=float)

        # Constrói a forma de onda bit a bit
        for b in bits:
            if b == 1:
                waveform = np.append(waveform, carrier_1)
            else:
                waveform = np.append(waveform, carrier_0)

        t = np.arange(len(waveform)) / self.fs
        return t, waveform

    def decode_fsk(self, waveform):
        """Decodificador FSK não-coerente (baseado em energia)"""
        s = self.samples_per_bit
        nb = len(waveform) // s
        bits = []

        # Cria vetores de tempo e referências (seno/cosseno) uma vez
        t_bit = np.arange(s) / self.fs
        ref_sin_f1 = np.sin(2 * np.pi * self.f1_fsk * t_bit)
        ref_cos_f1 = np.cos(2 * np.pi * self.f1_fsk * t_bit)
        ref_sin_f2 = np.sin(2 * np.pi * self.f2_fsk * t_bit)
        ref_cos_f2 = np.cos(2 * np.pi * self.f2_fsk * t_bit)

        for i in range(nb):
            chunk = waveform[i * s:(i + 1) * s]

            # Calcula a energia na frequência f1
            corr_sin_f1 = np.sum(chunk * ref_sin_f1)
            corr_cos_f1 = np.sum(chunk * ref_cos_f1)
            energy_f1 = corr_sin_f1 ** 2 + corr_cos_f1 ** 2

            # Calcula a energia na frequência f2
            corr_sin_f2 = np.sum(chunk * ref_sin_f2)
            corr_cos_f2 = np.sum(chunk * ref_cos_f2)
            energy_f2 = corr_sin_f2 ** 2 + corr_cos_f2 ** 2

            # Decide o bit com base na maior energia
            bits.append(1 if energy_f1 > energy_f2 else 0)

        return bits

    def qpsk(self, bits):
        simbolos = self.bits_to_symbols(bits, 'QPSK') # Agrupamento de 2 bits por símbolo
        samples_per_symbol = 2 * self.samples_per_bit
        Ts = 2 * self.Tb  # Duração do símbolo
        fs = self.fs
        fc = 1/Ts  # 1 ciclo por símbolo (Nyquist)

        waveform = np.zeros(len(simbolos) * samples_per_symbol, dtype=float)

        # Gray mapping
        mapping = {
            (0, 0): (self.V, self.V), # Fase: 45º
            (0, 1): (-self.V, self.V), # Fase: 135º
            (1, 1): (-self.V, -self.V), # Fase: 225º
            (1, 0): (self.V, -self.V) # Fase: 315º
        }

        for i, simb in enumerate(simbolos):
            t_local = np.arange(0, samples_per_symbol) / fs

            # Geração de Portadora
            I_t = np.sqrt(2 / Ts) * np.cos(2 * np.pi * fc * t_local)
            Q_t = -np.sqrt(2 / Ts) * np.sin(2 * np.pi * fc * t_local)

            aI, aQ = mapping[simb] # x(t) e y(t)

            # Portadora modulada
            s = aI * I_t + aQ * Q_t

            inicio = i * samples_per_symbol
            fim = inicio + samples_per_symbol
            waveform[inicio:fim] = s

        t = np.arange(len(waveform)) / fs
        return t, waveform

    def decode_qpsk(self, waveform):
        samples_per_symbol = 2 * self.samples_per_bit
        Ts = 2 * self.Tb
        fs = self.fs
        fc = 1/Ts

        num_symbols = len(waveform) // samples_per_symbol
        bits = []

        for i in range(num_symbols):
            inicio = i * samples_per_symbol
            fim = inicio + samples_per_symbol
            simbolo = waveform[inicio:fim]

            t_local = np.arange(0, samples_per_symbol) / fs

            I_t = np.sqrt(2 / Ts) * np.cos(2 * np.pi * fc * t_local)
            Q_t = -np.sqrt(2 / Ts) * np.sin(2 * np.pi * fc * t_local)

            # Correlações (projeções)
            corr_I = np.sum(simbolo * I_t)
            corr_Q = np.sum(simbolo * Q_t)

            # Normalização
            E = np.sum(I_t ** 2)  # Energia da portadora
            I_hat = corr_I / E
            Q_hat = corr_Q / E

            # Gray mapping
            if I_hat > 0 and Q_hat > 0:
                bits.extend([0, 0])
            elif I_hat < 0 and Q_hat > 0:
                bits.extend([0, 1])
            elif I_hat < 0 and Q_hat < 0:
                bits.extend([1, 1])
            else:  # I_hat > 0 and Q_hat < 0
                bits.extend([1, 0])

        return bits

    # -------------------------
    # Modulador (Ex 1.1.2) 16-QAM
    # -------------------------
    def st_qam(self, bits):
        simbolos = self.bits_to_symbols(bits, '16-QAM') # Agrupamento de 4 bits por símbolo
        samples_per_symbol = 4 * self.samples_per_bit
        Ts = 4 * self.Tb
        fs = self.fs
        fc = 1 / Ts

        waveform = np.zeros(len(simbolos) * samples_per_symbol, dtype=float)

        # Níveis da constelação 16-QAM quadrada
        sqrt2 = np.sqrt(2)
        level1 = -1 / sqrt2 * self.V      # -1/√2
        level2 = -1 / (3 * sqrt2) * self.V # -1/(3√2)
        level3 = 1 / (3 * sqrt2) * self.V  # +1/(3√2)
        level4 = 1 / sqrt2 * self.V       # +1/√2

        # Gray mapping
        mapping = {
            (0, 0, 0, 0): (level2, level2),  # -1/(3√2), -1/(3√2)
            (0, 0, 0, 1): (level2, level1),  # -1/(3√2), -1/√2
            (0, 0, 1, 1): (level2, level3),  # -1/(3√2), +1/(3√2)
            (0, 0, 1, 0): (level2, level4),  # -1/(3√2), +1/√2
            (0, 1, 0, 0): (level1, level2),  # -1/√2, -1/(3√2)
            (0, 1, 0, 1): (level1, level1),  # -1/√2, -1/√2
            (0, 1, 1, 1): (level1, level3),  # -1/√2, +1/(3√2)
            (0, 1, 1, 0): (level1, level4),  # -1/√2, +1/√2
            (1, 1, 0, 0): (level3, level2),  # +1/(3√2), -1/(3√2)
            (1, 1, 0, 1): (level3, level1),  # +1/(3√2), -1/√2
            (1, 1, 1, 1): (level3, level3),  # +1/(3√2), +1/(3√2)
            (1, 1, 1, 0): (level3, level4),  # +1/(3√2), +1/√2
            (1, 0, 0, 0): (level4, level2),  # +1/√2, -1/(3√2)
            (1, 0, 0, 1): (level4, level1),  # +1/√2, -1/√2
            (1, 0, 1, 1): (level4, level3),  # +1/√2, +1/(3√2)
            (1, 0, 1, 0): (level4, level4),  # +1/√2, +1/√2
        }

        for i, simb in enumerate(simbolos):
            aI, aQ = mapping[simb]

            t_local = np.arange(0, samples_per_symbol) / fs
            I_t = np.sqrt(2 / Ts) * np.cos(2 * np.pi * fc * t_local)
            Q_t = -np.sqrt(2 / Ts) * np.sin(2 * np.pi * fc * t_local)

            # s(t) = x(t)cos(2pifct) - y(t)sin(2pifct)
            s = aI * I_t + aQ * Q_t

            ini = i * samples_per_symbol
            fim = ini + samples_per_symbol
            waveform[ini:fim] = s

        t = np.arange(len(waveform)) / fs
        return t, waveform

    def decode_st_qam(self, waveform):
        samples_per_symbol = 4 * self.samples_per_bit
        Ts = 4 * self.Tb
        fs = self.fs
        fc = 1 / Ts

        num_symbols = len(waveform) // samples_per_symbol
        bits = []

        # Níveis da constelação (4 níveis por eixo)
        """ 
        índice 0: -1/√2 (level1)
        índice 1: -1/(3√2) (level2)
        índice 2: +1/(3√2) (level3)
        índice 3: +1/√2 (level4)
        """
        sqrt2 = np.sqrt(2)
        levels = np.array([-1 / sqrt2 * self.V, -1 / (3 * sqrt2) * self.V, 1 / (3 * sqrt2) * self.V, 1 / sqrt2 * self.V])

        # Mapeamento inverso Gray
        inverse_mapping = {
            (1, 1): (0, 0, 0, 0),  # level2, level2
            (1, 0): (0, 0, 0, 1),  # level2, level1
            (1, 2): (0, 0, 1, 1),  # level2, level3
            (1, 3): (0, 0, 1, 0),  # level2, level4
            (0, 1): (0, 1, 0, 0),  # level1, level2
            (0, 0): (0, 1, 0, 1),  # level1, level1
            (0, 2): (0, 1, 1, 1),  # level1, level3
            (0, 3): (0, 1, 1, 0),  # level1, level4
            (2, 1): (1, 1, 0, 0),  # level3, level2
            (2, 0): (1, 1, 0, 1),  # level3, level1
            (2, 2): (1, 1, 1, 1),  # level3, level3
            (2, 3): (1, 1, 1, 0),  # level3, level4
            (3, 1): (1, 0, 0, 0),  # level4, level2
            (3, 0): (1, 0, 0, 1),  # level4, level1
            (3, 2): (1, 0, 1, 1),  # level4, level3
            (3, 3): (1, 0, 1, 0),  # level4, level4
        }

        for i in range(num_symbols):
            ini = i * samples_per_symbol
            fim = ini + samples_per_symbol
            simbolo = waveform[ini:fim]

            t_local = np.arange(0, samples_per_symbol) / fs
            I_t = np.sqrt(2 / Ts) * np.cos(2 * np.pi * fc * t_local)
            Q_t = -np.sqrt(2 / Ts) * np.sin(2 * np.pi * fc * t_local)

            # Correlação (extração I(t) e Q(t))
            corr_I = np.sum(simbolo * I_t)
            corr_Q = np.sum(simbolo * Q_t)
            E = np.sum(I_t ** 2)

            I_hat = corr_I / E
            Q_hat = corr_Q / E

            # Quantização em 4 níveis (decisão pelo nível mais próximo)
            I_idx = np.argmin(np.abs(I_hat - levels))
            Q_idx = np.argmin(np.abs(Q_hat - levels))

            # Conversão para bits usando mapeamento inverso
            if (I_idx, Q_idx) in inverse_mapping:
                symbol_bits = inverse_mapping[(I_idx, Q_idx)]
                bits.extend(symbol_bits)
            else:
                # Fallback para símbolos não mapeados
                bits.extend([0, 0, 0, 0])

        return bits
