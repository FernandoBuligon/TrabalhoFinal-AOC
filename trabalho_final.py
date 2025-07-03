from tkinter import *
from tkinter import ttk
import random
import collections

class MainPage(Frame):
    """Representa a tela do menu principal da aplicação."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg='#1a202c') # Inicia o frame, que é a base da tela
        self.controller = controller # Guarda o "controlador" principal para poder trocar de tela
        self.grid_rowconfigure((0, 3), weight=1) # Faz as linhas de cima e de baixo expandirem, centralizando o conteúdo
        self.grid_rowconfigure((1, 2), weight=0)
        self.grid_columnconfigure(0, weight=1) # Faz a coluna expandir para ocupar a janela toda

        Label(self, text="Simulador de Gerenciamento de Memória", font=("Inter", 28, "bold"), fg="#e2e8f0", bg=self.cget('bg')).grid(row=1, column=0, pady=(50, 20), sticky="n")

        area_texto = Text(self, wrap="word", bg=self.cget('bg'), fg="#a0aec0", font=("Inter", 12),
                         padx=50, pady=20, height=8, relief="flat")
        area_texto.insert(END, "Este aplicativo permite simular dois modelos de gerenciamento de memória:\n\n")
        area_texto.insert(END, "1. Overlay:", "bold_tag") # Adiciona texto com uma "tag" para estilização
        area_texto.insert(END, " Um modelo mais simples, onde os processos são carregados na memória de forma direta, ocupando espaços definidos.\n\n")
        area_texto.insert(END, "2. Paginação de Memória:", "bold_tag")
        area_texto.insert(END, " Um modelo mais avançado, onde os processos são divididos em páginas e alocados em quadros de memória.")
        area_texto.tag_configure("bold_tag", font=("Inter", 12, "bold"), foreground="#e2e8f0") # Configura como a tag "bold_tag" vai aparecer
        area_texto.config(state=DISABLED) # Desabilita a edição do texto
        area_texto.grid(row=2, column=0, pady=20, sticky="ew")

        frame_botoes = Frame(self, bg=self.cget('bg'))
        frame_botoes.grid(row=3, column=0, pady=(20, 50), sticky="n")
        
        # O lambda é usado aqui para que a função mostrar_tela seja chamada só quando o botão for clicado
        ttk.Button(frame_botoes, text="Ir para Overlay", command=lambda: controller.mostrar_tela("OverlaySimulator")).grid(row=0, column=0, padx=20, pady=10)
        ttk.Button(frame_botoes, text="Ir para Paginação", command=lambda: controller.mostrar_tela("PagingSimulator")).grid(row=0, column=1, padx=20, pady=10)

class OverlaySimulator(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg='#1a202c')
        self.controller = controller

        self.blocos_memoria = [] 
        self.processos_ativos = {} # processos ativos
        self.fila_processos = [] # fila de espera
        self.processos_concluidos = [] # processos concluidos
        self.contagem_processos = {} # aux para limitar processos a uma execucao
        self.principal_terminou_esperando = False # bool que indica o final do processo principal
        self.id_job_simulacao = None # id do loop de simulação
        self.ids_animacao = {} # guarda os ids da animação de cada processo

        self.criar_elementos() # Chama a função que desenha a tela
        self.reiniciar_simulacao_e_interface() # Reseta tudo para o estado inicial

    def criar_elementos(self):
        self.grid_rowconfigure((0, 1), weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        frame_cabecalho = Frame(self, bg=self.cget('bg'))
        frame_cabecalho.grid(row=0, column=0, pady=10, sticky="ew")
        Label(frame_cabecalho, text="Simulador de Overlay", font=("Inter", 20, "bold"), fg="#e2e8f0", bg=frame_cabecalho.cget('bg')).pack()
        
        estilo = ttk.Style()
        estilo.configure("LightButton.TButton", font=("Inter", 11, "bold"), padding=8, relief="flat", background="#4299e1", foreground="black")
        estilo.map("LightButton.TButton", background=[('active', '#3182ce')])
        ttk.Button(frame_cabecalho, text="Voltar ao Menu", command=lambda: self.controller.mostrar_tela("MainPage"), style="LightButton.TButton").pack(pady=5)

        frame_controles = Frame(self, bg="#2d3748", padx=20, pady=10, relief="raised", bd=2, highlightbackground="#4a5568", highlightthickness=1)
        frame_controles.grid(row=1, column=0, pady=10, padx=20, sticky="ew")
        frame_controles.grid_columnconfigure((0, 1), weight=1)

        self.botao_iniciar = ttk.Button(frame_controles, text="Iniciar Simulação", command=self.iniciar_simulacao, style="LightButton.TButton")
        self.botao_iniciar.grid(row=0, column=0, padx=10, pady=5)
        
        estilo.configure("Red.TButton", font=("Inter", 11, "bold"), padding=8, relief="flat", background="#e53e3e", foreground="white")
        estilo.map("Red.TButton", background=[('active', '#c53030')])
        self.botao_parar = ttk.Button(frame_controles, text="Parar Simulação", command=self.parar_simulacao, style="Red.TButton", state=DISABLED)
        self.botao_parar.grid(row=0, column=1, padx=10, pady=5)

        area_simulacao = Frame(self, bg=self.cget('bg'))
        area_simulacao.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        area_simulacao.grid_columnconfigure(0, weight=3)
        area_simulacao.grid_columnconfigure(1, weight=1)
        area_simulacao.grid_rowconfigure(0, weight=1)

        frame_visual_memoria = Frame(area_simulacao, bg="#2d3748", relief="raised", bd=2, highlightbackground="#4a5568", highlightthickness=1)
        frame_visual_memoria.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        Label(frame_visual_memoria, text="Memória Principal (Overlay)", font=("Inter", 16, "bold"), fg="#e2e8f0", bg=frame_visual_memoria.cget('bg')).pack(pady=10)
        
        container_blocos = Frame(frame_visual_memoria, bg=frame_visual_memoria.cget('bg'))
        container_blocos.pack(expand=True, fill="both", padx=10, pady=(0, 10))
        for i in range(5):
            container_blocos.grid_columnconfigure(i, weight=1)
        container_blocos.grid_rowconfigure(0, weight=1)

        # Loop para criar os 5 blocos de memória visuais
        for i in range(5):
            wrapper_bloco = Frame(container_blocos, bg=container_blocos.cget('bg'))
            wrapper_bloco.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            wrapper_bloco.grid_rowconfigure(0, weight=1)
            wrapper_bloco.grid_columnconfigure(0, weight=1)

            bloco = Frame(wrapper_bloco, width=150, height=150, bg="#A7A3A3", relief="flat")
            bloco.pack(expand=True, fill="both", padx=5, pady=5)

            barra_progresso = Frame(bloco, bg="#4caf50") # Cria a barrinha verde de progresso
            barra_progresso.place(relx=0, rely=1, relwidth=1, relheight=0, anchor="sw") # Posiciona no canto inferior, com altura 0
            
            label_bloco = Label(wrapper_bloco, text="", bg="#A7A3A3", fg="black", font=("Inter", 10, "bold"), wraplength=100, padx=5, pady=5)
            label_bloco.pack(fill="x", pady=(0,5), padx=5)

            # Adiciona um dicionário com as informações do bloco na nossa lista de controle
            self.blocos_memoria.append({"bloco": bloco, "barra_progresso": barra_progresso, "label": label_bloco, "ocupado": False, "id_processo": None})
        
        self.blocos_memoria[0]["ocupado"] = True

        frame_listas = Frame(area_simulacao, bg=self.cget('bg'))
        frame_listas.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        frame_listas.grid_rowconfigure((0, 1), weight=1)
        frame_listas.grid_columnconfigure(0, weight=1)

        frame_fila = Frame(frame_listas, bg="#2d3748", relief="raised", bd=2, highlightbackground="#4a5568", highlightthickness=1)
        frame_fila.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        Label(frame_fila, text="Próximos Processos", font=("Inter", 14, "bold"), fg="#e2e8f0", bg=frame_fila.cget('bg')).pack(pady=5)
        self.label_fila = Text(frame_fila, wrap="word", bg="#2d3748", fg="#e2e8f0", height=8, padx=10, pady=10, font=("Inter", 10), relief="flat", state=DISABLED)
        self.label_fila.pack(expand=True, fill="both", padx=10, pady=(0,10))

        frame_concluidos = Frame(frame_listas, bg="#2d3748", relief="raised", bd=2, highlightbackground="#4a5568", highlightthickness=1)
        frame_concluidos.grid(row=1, column=0, sticky="nsew")
        Label(frame_concluidos, text="Processos Finalizados", font=("Inter", 14, "bold"), fg="#e2e8f0", bg=frame_concluidos.cget('bg')).pack(pady=5)
        self.label_concluidos = Text(frame_concluidos, wrap="word", bg="#2d3748", fg="#e2e8f0", height=8, padx=10, pady=10, font=("Inter", 10), relief="flat", state=DISABLED)
        self.label_concluidos.pack(expand=True, fill="both", padx=10, pady=(0,10))

    @staticmethod
    def pegar_tempo_execucao(nome_processo):
        """Retorna um tempo de execução fixo para cada processo."""
        tempos = {
            'Processo Principal': 10000, 'Subrotina 1': 5000, 'Subrotina 2': 4000,
            'Subrotina 3': 6000, 'Subrotina 4': 8000, 'Subrotina 5': 3000,
            'Subrotina 6': 5000, 'Subrotina 7': 7000, 'Subrotina 8': 3000,
            'Subrotina 9': 9000, 'Subrotina 10': 4000
        }
        return tempos.get(nome_processo, 5000)

    def pode_rodar_processo(self, nome_processo):
        return self.contagem_processos.get(nome_processo, 0) < 1

    def contar_execucao_processo(self, nome_processo):
        self.contagem_processos[nome_processo] = self.contagem_processos.get(nome_processo, 0) + 1

    def reiniciar_simulacao_e_interface(self):
        if self.id_job_simulacao:
            self.after_cancel(self.id_job_simulacao) # Para qualquer loop de simulação agendado
            self.id_job_simulacao = None
        
        for job_id in self.ids_animacao.values():
            if job_id: self.after_cancel(job_id)
        self.ids_animacao.clear()

        # Limpa as listas de controle
        self.processos_concluidos.clear()
        self.processos_ativos.clear()
        self.contagem_processos.clear()
        self.principal_terminou_esperando = False
        
        # Reinicia a aparência e estado de cada bloco de memória
        for i, info_bloco in enumerate(self.blocos_memoria):
            info_bloco["barra_progresso"].place(relx=0, rely=1, relwidth=1, relheight=0, anchor="sw")
            if i == 0:
                info_bloco["label"].config(text="Processo Principal", bg="#4b3dbc", fg="white")
                info_bloco["bloco"].config(bg="#A8DADC")
                info_bloco["ocupado"] = True
                info_bloco["id_processo"] = "Processo Principal"
            else:
                info_bloco["label"].config(text="Espaço Livre", bg="#A7A3A3", fg="black")
                info_bloco["bloco"].config(bg="#A7A3A3")
                info_bloco["ocupado"] = False
                info_bloco["id_processo"] = None

        # Recria a fila inicial de processos
        self.fila_processos = [{"nome": f"Subrotina {i}", "id": f"Sub_{i}_{random.randint(1,1000)}"} for i in range(1, 11)]
        self.fila_processos.insert(0, {"nome": "Processo Principal", "id": "proc_principal_unico"})

        self.atualizar_listas() # Atualiza as listas na tela (Fila e Concluídos)
        
        estilo = ttk.Style()
        estilo.configure("completed.TButton", font=("Inter", 11, "bold"), padding=8, relief="flat", background="#4CAF50", foreground="white")
        estilo.map("completed.TButton", background=[('active', '#388E3C')])
        
        self.botao_iniciar.config(text="Iniciar Simulação", state=NORMAL, style="LightButton.TButton")
        self.botao_parar.config(state=DISABLED)
        print("Simulador de Overlay reiniciado! Tudo pronto.")

    def iniciar_simulacao(self):
        self.reiniciar_simulacao_e_interface() # Garante que tudo comece do zero
        self.botao_iniciar.config(state=DISABLED)
        self.botao_parar.config(state=NORMAL)
        self.tentar_alocar_processo() # Faz a primeira tentativa de colocar processos na memória
        if not self.id_job_simulacao:
            # Agenda o loop principal da simulação para rodar a cada 500ms
            self.id_job_simulacao = self.after(500, self.loop_de_atualizacao)

    def parar_simulacao(self):
        if self.id_job_simulacao:
            self.after_cancel(self.id_job_simulacao) # Cancela o loop agendado
            self.id_job_simulacao = None
        self.reiniciar_simulacao_e_interface() # Volta a tela para o estado inicial
        print("Simulação de Overlay parada pelo usuário.")

    def tentar_alocar_processo(self):
        """Verifica se há espaço na memória e processos na fila para alocar."""
        if not self.id_job_simulacao: return

        if not any(p.get("name") == "Processo Principal" for p in self.processos_ativos.values()):
            if self.pode_rodar_processo("Processo Principal"):
                proc_principal = next((p for p in self.fila_processos if p["nome"] == "Processo Principal"), None)
                if proc_principal:
                    self.fila_processos.remove(proc_principal)
                    self.executar_processo(proc_principal, 0)
        
        for i in range(1, 5):
            if not self.blocos_memoria[i]["ocupado"] and self.fila_processos: # Se o bloco está livre e tem gente na fila...
                processo = next((p for p in self.fila_processos if "Subrotina" in p["nome"]), None)
                if processo:
                    self.fila_processos.remove(processo) # Tira da fila
                    self.executar_processo(processo, i) # Coloca para executar na memória
        
        self.atualizar_listas()

    def executar_processo(self, info_processo, indice_bloco):
        nome = info_processo["nome"]
        info_bloco = self.blocos_memoria[indice_bloco]

        cores_claras = ["#FFADAD", "#FFD6A5", "#FDFFB6", "#CAFFBF", "#9BF6FF"]
        cor_selecionada = "#A8DADC" if nome == "Processo Principal" else random.choice(cores_claras)
            
        info_bloco["ocupado"] = True
        info_bloco["id_processo"] = info_processo["id"]
        info_bloco["label"].config(text=nome, bg=cor_selecionada, fg="black")
        info_bloco["bloco"].config(bg=cor_selecionada)

        duracao_total_ms = self.pegar_tempo_execucao(nome)
        
        self.processos_ativos[indice_bloco] = {
            "name": nome, "id": info_processo["id"], "remaining_ms": duracao_total_ms
        }
        self.contar_execucao_processo(nome) # Marca que este processo já rodou uma vez

        # Função interna para animar a barra de progresso
        def atualizar_progresso(duracao_inicial=duracao_total_ms):
            id_animacao = self.ids_animacao.get(info_processo["id"])
            if not id_animacao or not self.id_job_simulacao: return

            processo_ativo = self.processos_ativos.get(indice_bloco)
            if not processo_ativo or processo_ativo["id"] != info_processo["id"]: return # Se o processo não está mais ativo, para a animação

            processo_ativo["remaining_ms"] -= 100 # Diminui o tempo restante
            if processo_ativo["remaining_ms"] > 0:
                porcentagem = 1 - (processo_ativo["remaining_ms"] / duracao_inicial) # Calcula o progresso
                info_bloco["barra_progresso"].place(relx=0, rely=1, relwidth=1, relheight=porcentagem, anchor="sw") # Atualiza a altura da barra
                self.ids_animacao[info_processo["id"]] = self.after(100, atualizar_progresso, duracao_inicial) # Agenda a próxima atualização
            else:
                self.finalizar_processo(info_processo, indice_bloco) # Se o tempo acabou, finaliza

        # Inicia o ciclo de animação
        self.ids_animacao[info_processo["id"]] = self.after(100, atualizar_progresso)

    def finalizar_processo(self, info_processo, indice_bloco):
        nome = info_processo["nome"]
        
        if indice_bloco in self.processos_ativos and self.processos_ativos[indice_bloco]["id"] == info_processo["id"]:
            del self.processos_ativos[indice_bloco]
            
            info_bloco = self.blocos_memoria[indice_bloco]
            info_bloco["ocupado"] = False
            info_bloco["id_processo"] = None
            info_bloco["barra_progresso"].place(relx=0, rely=1, relwidth=1, relheight=0, anchor="sw")
            
            if indice_bloco != 0:
                 info_bloco["label"].config(text="Espaço Livre", bg="#A7A3A3", fg="black")
                 info_bloco["bloco"].config(bg="#A7A3A3")

        if info_processo["id"] in self.ids_animacao:
            del self.ids_animacao[info_processo["id"]]

        self.processos_concluidos.append(info_processo) # Adiciona à lista de processos finalizados
        
        if nome == "Processo Principal":
            self.principal_terminou_esperando = True # Sinaliza que o principal acabou
        
        self.verificar_fim_simulacao() # Checa se a simulação toda pode acabar
        self.atualizar_listas()

    def verificar_fim_simulacao(self):
        if not self.principal_terminou_esperando: return
        
        # Conta quantas sub-rotinas únicas já foram concluídas
        subrotinas_concluidas_count = len([p for p in self.processos_concluidos if "Subrotina" in p["nome"]])
        
        if subrotinas_concluidas_count >= 10: # Se todas as 10 já rodaram
            self.marcar_simulacao_como_concluida()

    def marcar_simulacao_como_concluida(self):
        if self.id_job_simulacao:
            self.after_cancel(self.id_job_simulacao)
            self.id_job_simulacao = None
        self.botao_iniciar.config(text="Simulação Concluída!", state=DISABLED, style="completed.TButton")
        self.botao_parar.config(state=DISABLED)
        print("terminou hihihihihi")

    def atualizar_listas(self):
        self.label_fila.config(state=NORMAL)
        self.label_fila.delete("1.0", END)
        if self.fila_processos:
            for info_proc in self.fila_processos[:10]:
                self.label_fila.insert(END, f"{info_proc['nome']}\n", ("cor_fila",))
            self.label_fila.tag_configure("cor_fila", foreground="#B8BEBB")
        else:
            self.label_fila.insert(END, "Fila vazia.\n", ("texto_normal",))
        self.label_fila.config(state=DISABLED)

        self.label_concluidos.config(state=NORMAL)
        self.label_concluidos.delete("1.0", END)
        if self.processos_concluidos:
            for info_proc in self.processos_concluidos:
                self.label_concluidos.insert(END, f"{info_proc['nome']}\n", ("cor_concluido",))
            self.label_concluidos.tag_configure("cor_concluido", foreground="#3D9140")
        else:
            self.label_concluidos.insert(END, "Nenhum processo finalizado ainda.\n", ("texto_normal",))
        self.label_concluidos.config(state=DISABLED)
        
        self.label_fila.tag_configure("texto_normal", foreground="#a0aec0")
        self.label_concluidos.tag_configure("texto_normal", foreground="#a0aec0")

    def loop_de_atualizacao(self):
        """É o "coração" da simulação, roda periodicamente."""
        self.tentar_alocar_processo() # A cada "batida", tenta alocar novos processos
        self.atualizar_listas() # E atualiza a interface
        if self.id_job_simulacao:
            # Reagenda a si mesmo para a próxima "batida"
            self.id_job_simulacao = self.after(500, self.loop_de_atualizacao)

class PagingSimulator(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg='#1a202c')
        self.controller = controller

        self.quadros_memoria = []
        self.processos = {} 
        self.fila_processos = collections.deque()
        self.processos_ativos = []
        self.processos_concluidos = []
        self.simulacao_rodando = False
        self.id_job_simulacao = None
        self.cores_dos_processos = {}
        self.mapa_processo_quadro = {} 
        self.proximo_id_processo = 1

        self.criar_elementos()
        self.reiniciar_simulacao_e_interface()

    def criar_elementos(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        frame_cabecalho = Frame(self, bg=self.cget('bg'))
        frame_cabecalho.grid(row=0, column=0, pady=10, sticky="ew")
        Label(frame_cabecalho, text="Simulador de Paginação de Memória", font=("Inter", 20, "bold"), fg="#e2e8f0", bg=frame_cabecalho.cget('bg')).pack()
        ttk.Button(frame_cabecalho, text="Voltar ao Menu", command=lambda: self.controller.mostrar_tela("MainPage"), style="LightButton.TButton").pack(pady=5)

        frame_controles = Frame(self, bg="#2d3748", padx=20, pady=10, relief="raised", bd=2, highlightbackground="#4a5568", highlightthickness=1)
        frame_controles.grid(row=1, column=0, pady=10, padx=20, sticky="ew")
        frame_controles.grid_columnconfigure((0, 1, 2), weight=1)

        self.botao_iniciar = ttk.Button(frame_controles, text="Iniciar Simulação", command=self.iniciar_simulacao, style="LightButton.TButton")
        self.botao_iniciar.grid(row=0, column=0, padx=10, pady=5)
        self.botao_parar = ttk.Button(frame_controles, text="Parar Simulação", command=self.parar_simulacao, style="Red.TButton", state=DISABLED)
        self.botao_parar.grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(frame_controles, text="Resetar Simulação", command=self.reiniciar_simulacao_e_interface, style="LightButton.TButton").grid(row=0, column=2, padx=10, pady=5)

        area_simulacao = Frame(self, bg=self.cget('bg'))
        area_simulacao.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        area_simulacao.grid_columnconfigure(0, weight=3)
        area_simulacao.grid_columnconfigure(1, weight=1)
        area_simulacao.grid_rowconfigure(0, weight=1)

        frame_visual_memoria = Frame(area_simulacao, bg="#2d3748", relief="raised", bd=2, highlightbackground="#4a5568", highlightthickness=1)
        frame_visual_memoria.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        Label(frame_visual_memoria, text="Memória Principal (Quadros)", font=("Inter", 16, "bold"), fg="#e2e8f0", bg=frame_visual_memoria.cget('bg')).pack(pady=10)
        
        container_quadros = Frame(frame_visual_memoria, bg=frame_visual_memoria.cget('bg'))
        container_quadros.pack(expand=True, fill="both", padx=10, pady=(0, 10))
        
        self.widgets_quadros_memoria = []
        num_colunas = 5
        num_linhas = (10 + num_colunas - 1) // num_colunas
        
        for i in range(num_linhas): container_quadros.grid_rowconfigure(i * 2 + 1, weight=1)
        for i in range(num_colunas): container_quadros.grid_columnconfigure(i, weight=1)

        for i in range(10):
            linha, coluna = divmod(i, num_colunas)
            
            label_quadro = Label(container_quadros, text=f"Q{i}\nLivre", bg="#A7A3A3", fg="black", font=("Inter", 8), justify=CENTER)
            label_quadro.grid(row=linha*2, column=coluna, padx=2, pady=(2,0), sticky="nsew")

            bloco_quadro = Frame(container_quadros, bg="#A7A3A3", relief="solid", bd=1)
            bloco_quadro.grid(row=linha*2+1, column=coluna, padx=2, pady=(0,2), sticky="nsew")
            
            barra_progresso = Frame(bloco_quadro, bg="#4CAF50")
            barra_progresso.place(relx=0, rely=1, relwidth=1, relheight=0, anchor="sw")

            self.widgets_quadros_memoria.append({"bloco": bloco_quadro, "label": label_quadro, "barra_progresso": barra_progresso})

        painel_listas_processos = Frame(area_simulacao, bg=self.cget('bg'))
        painel_listas_processos.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        painel_listas_processos.grid_rowconfigure((0, 1, 2), weight=1)
        painel_listas_processos.grid_columnconfigure(0, weight=1)

        self.label_fila = self._criar_lista_processos_widget(painel_listas_processos, "Processos em Fila", 0)
        self.label_ativas = self._criar_lista_processos_widget(painel_listas_processos, "Processos Ativos", 1)
        self.label_concluidas = self._criar_lista_processos_widget(painel_listas_processos, "Processos Finalizados", 2)
    
    def _criar_lista_processos_widget(self, parent, titulo, linha):
        frame = Frame(parent, bg="#2d3748", relief="raised", bd=2, highlightbackground="#4a5568", highlightthickness=1)
        frame.grid(row=linha, column=0, sticky="nsew", pady=(0, 10 if linha < 2 else 0))
        Label(frame, text=titulo, font=("Inter", 14, "bold"), fg="#e2e8f0", bg=frame.cget('bg')).pack(pady=5)
        widget_texto = Text(frame, wrap="word", bg="#2d3748", fg="#e2e8f0", height=6, padx=10, pady=10, font=("Inter", 9), relief="flat", state=DISABLED)
        widget_texto.pack(expand=True, fill="both", padx=10, pady=(0,10))
        widget_texto.tag_configure("texto_normal", foreground="#a0aec0")
        widget_texto.tag_configure("cor_concluido", foreground="#3D9140")
        return widget_texto

    def pegar_cor_processo(self, id_processo):
        if id_processo not in self.cores_dos_processos:
            cores = ["#FFADAD", "#FFD6A5", "#FDFFB6", "#CAFFBF", "#9BF6FF", "#A2C38E", "#E6CCB2", "#D4A5A5"]
            self.cores_dos_processos[id_processo] = random.choice(cores)
        return self.cores_dos_processos[id_processo]

    def reiniciar_simulacao_e_interface(self):
        self.parar_simulacao()
        self.quadros_memoria = [{"id_processo": None, "num_pagina": None} for _ in range(10)]
        self.processos.clear()
        self.fila_processos.clear()
        self.processos_ativos.clear()
        self.processos_concluidos.clear()
        self.cores_dos_processos.clear()
        self.mapa_processo_quadro.clear()
        self.proximo_id_processo = 1
        
        # No reset, já cria os 10 processos que vão rodar
        for i in range(10):
            id_processo = self.gerar_processo_aleatorio()
            if id_processo: self.mapa_processo_quadro[id_processo] = i # Associa cada processo a um quadro fixo

        self.atualizar_interface()
        self.botao_iniciar.config(text="Iniciar Simulação", state=NORMAL, style="LightButton.TButton")
        self.botao_parar.config(state=DISABLED)
        print("Simulador de Paginação reiniciado!")

    def gerar_processo_aleatorio(self):
        """Cria um novo processo com um número aleatório de páginas."""
        if self.proximo_id_processo > 10: return None
        
        id_processo = f"P{self.proximo_id_processo}"
        self.proximo_id_processo += 1
        
        num_paginas = random.randint(5, 10)
        
        self.processos[id_processo] = {
            "nome": id_processo, "paginas": list(range(num_paginas)),
            "sequencia_acesso": list(range(num_paginas)), "indice_acesso_atual": 0, # A sequência de acesso será 0, 1, 2, ...
            "tabela_paginas": {}, "status": "na_fila", "cor": self.pegar_cor_processo(id_processo),
            'tempo_prox_acesso_pagina': 0,
            'duracao_processamento_pagina_ms': random.randint(4 * 1000,8 * 1000)
        }
        self.fila_processos.append(id_processo) # Adiciona o novo processo na fila de espera
        return id_processo

    def iniciar_simulacao(self):
        self.reiniciar_simulacao_e_interface()
        self.simulacao_rodando = True
        self.botao_iniciar.config(state=DISABLED)
        self.botao_parar.config(state=NORMAL)
        self.loop_simulacao()
        print("Começou! Simulação de Paginação iniciada.")

    def parar_simulacao(self):
        self.simulacao_rodando = False
        if self.id_job_simulacao:
            self.after_cancel(self.id_job_simulacao)
            self.id_job_simulacao = None
        self.botao_iniciar.config(state=NORMAL)
        self.botao_parar.config(state=DISABLED)

    def loop_simulacao(self):
        """O loop principal da simulação de paginação."""
        if not self.simulacao_rodando: return # Para o loop se a flag for falsa

        self.tentar_ativar_processos() # Tenta mover processos da fila para a memória
        
        # Para cada processo que está ativo...
        for id_processo in list(self.processos_ativos):
            processo = self.processos.get(id_processo)
            if not processo: continue

            processo['tempo_prox_acesso_pagina'] -= 200 # Diminui o contador de tempo
            if processo['tempo_prox_acesso_pagina'] <= 0: # Se o tempo zerou, é hora de acessar uma nova página
                if processo["indice_acesso_atual"] < len(processo["sequencia_acesso"]):
                    num_pagina = processo["sequencia_acesso"][processo["indice_acesso_atual"]]
                    self.lidar_com_acesso_pagina(id_processo, num_pagina) # Lida com o acesso (page fault/hit)
                    processo["indice_acesso_atual"] += 1
                    processo['tempo_prox_acesso_pagina'] = processo['duracao_processamento_pagina_ms'] # Reseta o timer
                else:
                    self.finalizar_processo(id_processo) # Se acabou a sequência, finaliza
        
        if not self.processos_ativos and not self.fila_processos and len(self.processos_concluidos) == 10:
            print("Show! Simulação de Paginação Concluída.")
            self.parar_simulacao()
            self.botao_iniciar.config(text="Simulação Concluída!", style="completed.TButton")
            return

        self.atualizar_interface() # Atualiza a tela com os novos estados
        self.id_job_simulacao = self.after(200, self.loop_simulacao) # Agenda a próxima execução do loop

    def tentar_ativar_processos(self):
        while self.fila_processos and len(self.processos_ativos) < 10:
            id_processo = self.fila_processos.popleft()
            processo = self.processos[id_processo]
            processo["status"] = "ativo"
            self.processos_ativos.append(id_processo)
            
            if processo["paginas"]:
                self.lidar_com_acesso_pagina(id_processo, processo["paginas"][0])
                processo["indice_acesso_atual"] = 1
                processo['tempo_prox_acesso_pagina'] = processo['duracao_processamento_pagina_ms']
            else:
                self.finalizar_processo(id_processo)

    def lidar_com_acesso_pagina(self, id_processo, num_pagina):
        """Simula o acesso a uma página, tratando o page fault."""
        indice_quadro = self.mapa_processo_quadro[id_processo] # Pega o quadro de memória dedicado a este processo
        dados_quadro = self.quadros_memoria[indice_quadro]
        processo = self.processos[id_processo]

        # Se a página que queremos não é a que já está no quadro, isso é um "Page Fault"
        if not (dados_quadro["id_processo"] == id_processo and dados_quadro["num_pagina"] == num_pagina):
            print(f"{id_processo}, Página {num_pagina}: Faltou a página no Quadro {indice_quadro}! Carregando...")
            
            pagina_antiga = dados_quadro["num_pagina"]
            if pagina_antiga is not None and pagina_antiga in processo["tabela_paginas"]:
                del processo["tabela_paginas"][pagina_antiga]

            # Coloca a nova página no quadro de memória
            dados_quadro["id_processo"] = id_processo
            dados_quadro["num_pagina"] = num_pagina
            processo["tabela_paginas"][num_pagina] = indice_quadro # Atualiza a tabela de páginas

    def finalizar_processo(self, id_processo):
        processo = self.processos[id_processo]
        if processo["status"] == "concluido": return

        processo["status"] = "concluido"
        if id_processo in self.processos_ativos: self.processos_ativos.remove(id_processo)
        self.processos_concluidos.append(id_processo)
        
        indice_quadro = self.mapa_processo_quadro.get(id_processo)
        if indice_quadro is not None:
            self.quadros_memoria[indice_quadro] = {"id_processo": None, "num_pagina": None}
            self.widgets_quadros_memoria[indice_quadro]["barra_progresso"].place(relx=0, rely=1, relwidth=1, relheight=0, anchor="sw")
        
        processo["tabela_paginas"].clear()

    def atualizar_interface(self):
        """Atualiza todos os componentes visuais da tela."""
        # Itera sobre os dados da memória
        for i, dados_quadro in enumerate(self.quadros_memoria):
            widget = self.widgets_quadros_memoria[i] # Pega o widget correspondente
            if dados_quadro["id_processo"]:
                # Pinta o quadro e atualiza o texto se estiver ocupado
                processo = self.processos[dados_quadro["id_processo"]]
                cor = processo["cor"]
                widget["bloco"].config(bg=cor)
                
                rgb = self.winfo_rgb(cor)
                luminosidade = (0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]) / 65535
                cor_texto = "black" if luminosidade > 0.6 else "white"
                
                widget["label"].config(bg=cor, fg=cor_texto, text=f"Q{i}\n{dados_quadro['id_processo']}\nPág {dados_quadro['num_pagina']}")
                
                duracao_total = processo['duracao_processamento_pagina_ms']
                preenchimento = 1 - (max(0, processo['tempo_prox_acesso_pagina']) / duracao_total) if duracao_total > 0 else 1
                widget["barra_progresso"].place(relx=0, rely=1, relwidth=1, relheight=preenchimento, anchor="sw")
            else:
                # Deixa cinza e com texto "Livre" se estiver vazio
                widget["bloco"].config(bg="#A7A3A3")
                widget["label"].config(bg="#A7A3A3", fg="black", text=f"Q{i}\nLivre")
                widget["barra_progresso"].place(relx=0, rely=1, relwidth=1, relheight=0, anchor="sw")
        
        # Atualiza as listas de texto da direita
        self._atualizar_lista_texto(self.label_fila, self.fila_processos, lambda p: f"{p['nome']} ({len(p['paginas'])} págs)", "Fila vazia.")
        self._atualizar_lista_texto(self.label_ativas, self.processos_ativos, lambda p: f"{p['nome']} (Próx: {'Pág ' + str(p['sequencia_acesso'][p['indice_acesso_atual']]) if p['indice_acesso_atual'] < len(p['sequencia_acesso']) else 'Fim'})", "Nenhum processo rodando.")
        self._atualizar_lista_texto(self.label_concluidas, self.processos_concluidos, lambda p: f"{p['nome']} (Finalizado!)", "Nenhum processo concluído.", concluido=True)

    def _atualizar_lista_texto(self, widget_texto, ids_processos, formatador, msg_vazio, concluido=False):
        widget_texto.config(state=NORMAL)
        widget_texto.delete("1.0", END)
        if ids_processos:
            for pid in ids_processos:
                processo = self.processos[pid]
                tag = f"cor_proc_{pid}"
                widget_texto.insert(END, f"{formatador(processo)}\n", (tag,))
                cor = "#3D9140" if concluido else processo["cor"]
                widget_texto.tag_configure(tag, foreground=cor)
        else:
            widget_texto.insert(END, msg_vazio + "\n", ("texto_normal",))
        widget_texto.config(state=DISABLED)

class MainApp(Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Simulador de Gerenciamento de Memória")
        self.geometry("1200x800")
        self.configure(background='#1a202c')
        self.minsize(1000, 700)

        container = Frame(self, bg=self.cget('bg')) # Um container para empilhar as telas
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {} # Um dicionário para guardar as instâncias de cada tela
        self.frame_atual = None # Guarda uma referência para a tela que está visível

        # Cria uma instância de cada tela e guarda no dicionário
        for F in (MainPage, OverlaySimulator, PagingSimulator):
            nome_pagina = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[nome_pagina] = frame
            frame.grid(row=0, column=0, sticky="nsew") # Coloca todas no mesmo lugar, uma em cima da outra

        self.mostrar_tela("MainPage") # Mostra a tela inicial

    def mostrar_tela(self, nome_da_tela):
        """Traz a tela desejada para a frente."""
        if self.frame_atual and self.frame_atual.__class__.__name__ == nome_da_tela:
            return

        frame = self.frames[nome_da_tela] # Pega a tela que queremos mostrar
        self.frame_atual = frame
        frame.tkraise() # Comando do Tkinter que joga a tela para o topo da pilha, tornando-a visível

        # Passa por todas as telas...
        for outra_tela in self.frames.values():
            # ... e se a tela não for a que estamos mostrando E ela tiver uma simulação...
            if outra_tela is not frame and hasattr(outra_tela, 'parar_simulacao'):
                outra_tela.parar_simulacao() # ...manda parar a simulação dela.
        
        # Reseta a simulação da nova tela que estamos mostrando para garantir que ela comece do zero
        if hasattr(frame, 'reiniciar_simulacao_e_interface'):
            frame.reiniciar_simulacao_e_interface()
            
if __name__ == "__main__":
    app = MainApp() # inicia a tela principal
    app.mainloop() # inicia o loop da aplicação