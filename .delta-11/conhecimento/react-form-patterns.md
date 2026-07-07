# React Form Patterns — Base de Conhecimento FORM

> **LIMITES ESTRUTURAIS E IDIOMA (obrigatório — `.delta-11/protocolos/regras-codigo.md` seções 8 e 9):**
> Função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · 1 classe por arquivo · complexidade ciclomática ≤ 10.
> Código em INGLÊS (nomes de variáveis, funções, tabelas, campos JSON) · conteúdo em PORTUGUÊS (comentários, textos de UI, mensagens ao usuário, descrições de teste). Nomes descritivos, sem abreviação.
> 1 schema Zod por formulário, compartilhado com o servidor · mensagens de validação em português, nomes de campos em inglês.


Referencia pratica para o agente FORM da Formacao Delta-11.
Foco: React Hook Form, Zod, validacao, multi-step, upload, acessibilidade.

---

## 1. React Hook Form — Setup Basico com Zod

```tsx
"use client"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"

const esquemaDeCadastro = z.object({
  nome: z.string().min(2, "Nome precisa ter pelo menos 2 letras"),
  email: z.string().email("Email invalido"),
  senha: z.string().min(8, "Senha precisa ter pelo menos 8 caracteres"),
  confirmarSenha: z.string(),
}).refine((dados) => dados.senha === dados.confirmarSenha, {
  message: "As senhas nao conferem",
  path: ["confirmarSenha"],
})

type DadosDeCadastro = z.infer<typeof esquemaDeCadastro>

function FormularioDeCadastro() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<DadosDeCadastro>({
    resolver: zodResolver(esquemaDeCadastro),
  })

  async function onSubmit(dados: DadosDeCadastro) {
    await fetch("/api/cadastro", {
      method: "POST",
      body: JSON.stringify(dados),
    })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <CampoDeTexto label="Nome" erro={errors.nome?.message} {...register("nome")} />
      <CampoDeTexto label="Email" tipo="email" erro={errors.email?.message} {...register("email")} />
      <CampoDeTexto label="Senha" tipo="password" erro={errors.senha?.message} {...register("senha")} />
      <CampoDeTexto label="Confirmar Senha" tipo="password"
        erro={errors.confirmarSenha?.message} {...register("confirmarSenha")} />
      <button type="submit" disabled={isSubmitting}
        className="w-full bg-blue-600 text-white py-3 rounded-lg disabled:opacity-50">
        {isSubmitting ? "Cadastrando..." : "Criar Conta"}
      </button>
    </form>
  )
}
```

---

## 2. Campo Reutilizavel com Validacao Visual

```tsx
import { forwardRef, InputHTMLAttributes } from "react"

type PropsDoCampo = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  erro?: string
  tipo?: string
}

const CampoDeTexto = forwardRef<HTMLInputElement, PropsDoCampo>(
  ({ label, erro, tipo = "text", id, ...props }, ref) => {
    const campoId = id || label.toLowerCase().replace(/\s+/g, "-")
    return (
      <div className="space-y-1">
        <label htmlFor={campoId} className="block text-sm font-medium text-gray-700">
          {label}
        </label>
        <input
          ref={ref}
          id={campoId}
          type={tipo}
          aria-invalid={!!erro}
          aria-describedby={erro ? `${campoId}-erro` : undefined}
          className={`
            w-full px-4 py-2 border rounded-lg transition-colors
            focus:outline-none focus:ring-2 focus:ring-offset-1
            ${erro
              ? "border-red-500 focus:ring-red-300"
              : "border-gray-300 focus:border-blue-500 focus:ring-blue-200"
            }
          `}
          {...props}
        />
        {erro && (
          <p id={`${campoId}-erro`} role="alert" className="text-sm text-red-600 mt-1">
            {erro}
          </p>
        )}
      </div>
    )
  }
)
CampoDeTexto.displayName = "CampoDeTexto"
```

---

## 3. Controller (para componentes customizados)

```tsx
import { Controller, useForm } from "react-hook-form"

// Quando o componente NAO aceita ref (ex: select customizado, date picker)
function FormularioComSelect() {
  const { control, handleSubmit } = useForm()

  return (
    <form onSubmit={handleSubmit(console.log)}>
      <Controller
        name="categoria"
        control={control}
        rules={{ required: "Selecione uma categoria" }}
        render={({ field, fieldState }) => (
          <div>
            <SelectCustomizado
              valor={field.value}
              aoMudar={field.onChange}
              opcoes={["Eletronicos", "Roupas", "Casa"]}
            />
            {fieldState.error && (
              <p className="text-sm text-red-600">{fieldState.error.message}</p>
            )}
          </div>
        )}
      />
    </form>
  )
}
```

---

## 4. Validacao em Tempo Real

```tsx
const { register, watch, formState: { errors } } = useForm<DadosDeCadastro>({
  resolver: zodResolver(esquemaDeCadastro),
  mode: "onChange",        // valida ao digitar
  // mode: "onBlur",      // valida ao sair do campo
  // mode: "onTouched",   // valida ao sair do campo, mas so depois do primeiro toque
})

// Indicador de forca de senha
const senha = watch("senha", "")

function IndicadorDeForcaDeSenha({ senha }: { senha: string }) {
  const forca = calcularForca(senha) // 0-4

  const cores = ["bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-lime-500", "bg-green-500"]
  const textos = ["Muito fraca", "Fraca", "Media", "Forte", "Muito forte"]

  return (
    <div className="space-y-1">
      <div className="flex gap-1">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className={`h-1.5 flex-1 rounded-full transition-colors ${
            i <= forca ? cores[forca] : "bg-gray-200"
          }`} />
        ))}
      </div>
      {senha && <p className="text-xs text-gray-500">{textos[forca]}</p>}
    </div>
  )
}
```

---

## 5. Multi-Step Form

```tsx
"use client"
import { useState } from "react"
import { useForm, FormProvider } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"

// Esquemas por etapa
const esquemaEtapa1 = z.object({ nome: z.string().min(2), email: z.string().email() })
const esquemaEtapa2 = z.object({ endereco: z.string().min(5), cidade: z.string().min(2) })
const esquemaEtapa3 = z.object({ cartao: z.string().min(16) })

const esquemas = [esquemaEtapa1, esquemaEtapa2, esquemaEtapa3]
const totalDeEtapas = esquemas.length

function FormularioMultiEtapas() {
  const [etapaAtual, setEtapaAtual] = useState(0)

  const metodos = useForm({
    resolver: zodResolver(esquemas[etapaAtual]),
    mode: "onBlur",
  })

  async function avancar() {
    const valido = await metodos.trigger()
    if (!valido) return
    if (etapaAtual < totalDeEtapas - 1) {
      setEtapaAtual(etapaAtual + 1)
    } else {
      // Ultima etapa — enviar
      metodos.handleSubmit(enviarFormulario)()
    }
  }

  function voltar() {
    if (etapaAtual > 0) setEtapaAtual(etapaAtual - 1)
  }

  return (
    <FormProvider {...metodos}>
      {/* Indicador de progresso */}
      <div className="flex gap-2 mb-6">
        {esquemas.map((_, i) => (
          <div key={i} className={`h-2 flex-1 rounded-full transition-colors ${
            i <= etapaAtual ? "bg-blue-600" : "bg-gray-200"
          }`} />
        ))}
      </div>

      <form onSubmit={(e) => e.preventDefault()}>
        {etapaAtual === 0 && <EtapaDadosPessoais />}
        {etapaAtual === 1 && <EtapaEndereco />}
        {etapaAtual === 2 && <EtapaPagamento />}

        <div className="flex justify-between mt-6">
          {etapaAtual > 0 && (
            <button type="button" onClick={voltar}
              className="px-4 py-2 text-gray-600 hover:text-gray-800">
              Voltar
            </button>
          )}
          <button type="button" onClick={avancar}
            className="ml-auto px-6 py-2 bg-blue-600 text-white rounded-lg">
            {etapaAtual === totalDeEtapas - 1 ? "Finalizar" : "Proximo"}
          </button>
        </div>
      </form>
    </FormProvider>
  )
}
```

---

## 6. File Upload

```tsx
const esquemaDeUpload = z.object({
  arquivo: z
    .instanceof(FileList)
    .refine((lista) => lista.length > 0, "Selecione um arquivo")
    .refine((lista) => lista[0]?.size <= 5_000_000, "Arquivo deve ter no maximo 5MB")
    .refine(
      (lista) => ["image/jpeg", "image/png", "image/webp"].includes(lista[0]?.type),
      "Formato aceito: JPG, PNG ou WebP"
    ),
})

function CampoDeUpload() {
  const { register, watch, formState: { errors } } = useForm({
    resolver: zodResolver(esquemaDeUpload),
  })

  const arquivo = watch("arquivo")
  const previa = arquivo?.[0] ? URL.createObjectURL(arquivo[0]) : null

  return (
    <div>
      <label className="
        flex flex-col items-center justify-center w-full h-48
        border-2 border-dashed border-gray-300 rounded-lg
        cursor-pointer hover:border-blue-500 hover:bg-blue-50
        transition-colors
      ">
        {previa ? (
          <img src={previa} alt="Previa" className="h-full object-contain rounded" />
        ) : (
          <>
            <UploadIcon className="h-10 w-10 text-gray-400" />
            <p className="text-sm text-gray-500 mt-2">Clique para enviar imagem</p>
            <p className="text-xs text-gray-400">JPG, PNG ou WebP (max 5MB)</p>
          </>
        )}
        <input type="file" accept="image/*" className="hidden" {...register("arquivo")} />
      </label>
      {errors.arquivo && (
        <p className="text-sm text-red-600 mt-1">{errors.arquivo.message as string}</p>
      )}
    </div>
  )
}
```

---

## 7. Error Display Patterns

```tsx
// INLINE — ao lado do campo (melhor para formularios curtos)
<CampoDeTexto label="Email" erro={errors.email?.message} {...register("email")} />

// TOAST — notificacao flutuante (melhor para erros de servidor)
import { toast } from "sonner" // ou react-hot-toast

async function onSubmit(dados: DadosDeCadastro) {
  try {
    await fetch("/api/cadastro", { method: "POST", body: JSON.stringify(dados) })
    toast.success("Conta criada com sucesso!")
  } catch {
    toast.error("Erro ao criar conta. Tente novamente.")
  }
}

// SUMMARY — resumo no topo do form (melhor para formularios longos)
function ResumoDeErros({ errors }: { errors: Record<string, { message?: string }> }) {
  const listaDeErros = Object.entries(errors).filter(([, v]) => v.message)
  if (listaDeErros.length === 0) return null

  return (
    <div role="alert" className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
      <p className="font-medium text-red-800">Corrija os erros abaixo:</p>
      <ul className="mt-2 list-disc list-inside text-sm text-red-600">
        {listaDeErros.map(([campo, erro]) => (
          <li key={campo}>{erro.message}</li>
        ))}
      </ul>
    </div>
  )
}
```

---

## 8. Accessibility

```tsx
// Regras essenciais:
// 1. Todo input DEVE ter um label associado (htmlFor + id)
// 2. Erros DEVEM usar aria-describedby + role="alert"
// 3. Campos invalidos DEVEM ter aria-invalid="true"
// 4. Campos obrigatorios DEVEM ter aria-required="true"
// 5. Focus DEVE ser gerenciado em erros e transicoes

// Gerenciamento de foco em erros
import { useEffect, useRef } from "react"

function useFocusOnFirstError(errors: Record<string, unknown>) {
  const formRef = useRef<HTMLFormElement>(null)

  useEffect(() => {
    if (Object.keys(errors).length > 0 && formRef.current) {
      const primeiroCampoComErro = formRef.current.querySelector<HTMLInputElement>(
        '[aria-invalid="true"]'
      )
      primeiroCampoComErro?.focus()
    }
  }, [errors])

  return formRef
}

// Campo acessivel completo
<div role="group" aria-labelledby="grupo-contato">
  <h3 id="grupo-contato" className="text-lg font-semibold mb-2">Dados de Contato</h3>
  <input
    id="email"
    type="email"
    aria-label="Endereco de email"
    aria-required="true"
    aria-invalid={!!errors.email}
    aria-describedby={errors.email ? "email-erro" : "email-ajuda"}
    {...register("email")}
  />
  <p id="email-ajuda" className="text-xs text-gray-500">Usaremos para enviar a confirmacao</p>
  {errors.email && <p id="email-erro" role="alert" className="text-sm text-red-600">{errors.email.message}</p>}
</div>
```

---

## 9. Optimistic UI

```tsx
"use client"
import { useState } from "react"

function FormularioDeComentario({ publicacaoId }: { publicacaoId: string }) {
  const [comentarios, setComentarios] = useState<Comentario[]>([])
  const { register, handleSubmit, reset } = useForm()

  async function onSubmit(dados: { texto: string }) {
    // 1. Adiciona IMEDIATAMENTE na lista (otimista)
    const comentarioTemporario: Comentario = {
      id: `temp-${Date.now()}`,
      texto: dados.texto,
      autor: "Voce",
      status: "enviando",
    }
    setComentarios((prev) => [...prev, comentarioTemporario])
    reset()

    try {
      // 2. Envia para o servidor
      const resposta = await fetch("/api/comentarios", {
        method: "POST",
        body: JSON.stringify({ publicacaoId, texto: dados.texto }),
      })
      const comentarioReal = await resposta.json()

      // 3. Substitui o temporario pelo real
      setComentarios((prev) =>
        prev.map((c) => (c.id === comentarioTemporario.id ? comentarioReal : c))
      )
    } catch {
      // 4. Se falhou, marca como erro (usuario pode tentar de novo)
      setComentarios((prev) =>
        prev.map((c) =>
          c.id === comentarioTemporario.id ? { ...c, status: "erro" } : c
        )
      )
    }
  }

  return (
    <div>
      <ul className="space-y-2 mb-4">
        {comentarios.map((c) => (
          <li key={c.id} className={c.status === "enviando" ? "opacity-50" : ""}>
            <span>{c.texto}</span>
            {c.status === "erro" && (
              <button className="text-red-500 text-xs ml-2">Tentar novamente</button>
            )}
          </li>
        ))}
      </ul>
      <form onSubmit={handleSubmit(onSubmit)} className="flex gap-2">
        <input {...register("texto")} placeholder="Escreva um comentario..."
          className="flex-1 px-4 py-2 border rounded-lg" />
        <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">
          Enviar
        </button>
      </form>
    </div>
  )
}
```
