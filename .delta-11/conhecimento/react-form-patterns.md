# React Form Patterns — Base de Conhecimento FORM

> **LIMITES ESTRUTURAIS E IDIOMA (obrigatório — `.delta-11/protocolos/regras-codigo.md` seções 8 e 9):**
> Função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · 1 classe por arquivo · complexidade ciclomática ≤ 10.
> Código em INGLÊS (nomes de variáveis, funções, tabelas, campos JSON) · conteúdo em PORTUGUÊS (comentários, textos de UI, mensagens ao usuário, descrições de teste). Nomes descritivos, sem abreviação.
> 1 schema Zod por formulário, compartilhado com o servidor · mensagens de validação em português, nomes de campos em inglês.


Referencia pratica para o agente FORM da Formacao Delta-11 (base OFICIAL do FORM — `perfis/FORM.json`; complemento: `react-next-overview.md`). v6.3: identificadores em ingles (regra §9), toda string com `.max()` e senha com `.max(128)` (regra §2), erro da API no formato unico D13.
Foco: React Hook Form, Zod, validacao, multi-step, upload, acessibilidade.

---

## 1. React Hook Form — Setup Basico com Zod

```tsx
"use client"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"

const signUpSchema = z.object({
  name: z.string().trim().min(2, "Nome precisa ter pelo menos 2 letras").max(100, "Nome pode ter no maximo 100 letras"),
  email: z.string().trim().toLowerCase().email("Email invalido").max(254, "Email muito longo"),
  password: z.string().min(8, "Senha precisa ter pelo menos 8 caracteres").max(128, "Senha pode ter no maximo 128 caracteres"),
  confirmPassword: z.string().max(128),
}).refine((formData) => formData.password === formData.confirmPassword, {
  message: "As senhas nao conferem",
  path: ["confirmPassword"],
})

type SignUpFormData = z.infer<typeof signUpSchema>

function SignUpForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignUpFormData>({
    resolver: zodResolver(signUpSchema),
  })

  async function onSubmit(formData: SignUpFormData) {
    const response = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
    })
    if (!response.ok) {
      // formato unico de erro da API (D13): { error: { code, message, details } }
      const { error } = await response.json()
      throw new Error(error?.message ?? "Erro ao criar conta")
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <TextField label="Nome" error={errors.name?.message} {...register("name")} />
      <TextField label="Email" type="email" error={errors.email?.message} {...register("email")} />
      <TextField label="Senha" type="password" error={errors.password?.message} {...register("password")} />
      <TextField label="Confirmar Senha" type="password"
        error={errors.confirmPassword?.message} {...register("confirmPassword")} />
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

type TextFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  error?: string
  type?: string
}

const TextField = forwardRef<HTMLInputElement, TextFieldProps>(
  ({ label, error, type = "text", id, ...props }, ref) => {
    const fieldId = id || label.toLowerCase().replace(/\s+/g, "-")
    return (
      <div className="space-y-1">
        <label htmlFor={fieldId} className="block text-sm font-medium text-gray-700">
          {label}
        </label>
        <input
          ref={ref}
          id={fieldId}
          type={type}
          aria-invalid={!!error}
          aria-describedby={error ? `${fieldId}-erro` : undefined}
          className={`
            w-full px-4 py-2 border rounded-lg transition-colors
            focus:outline-none focus:ring-2 focus:ring-offset-1
            ${error
              ? "border-red-500 focus:ring-red-300"
              : "border-gray-300 focus:border-blue-500 focus:ring-blue-200"
            }
          `}
          {...props}
        />
        {error && (
          <p id={`${fieldId}-erro`} role="alert" className="text-sm text-red-600 mt-1">
            {error}
          </p>
        )}
      </div>
    )
  }
)
TextField.displayName = "TextField"
```

---

## 3. Controller (para componentes customizados)

```tsx
import { Controller, useForm } from "react-hook-form"

// Quando o componente NAO aceita ref (ex: select customizado, date picker)
function CategorySelectForm() {
  const { control, handleSubmit } = useForm()

  return (
    <form onSubmit={handleSubmit(console.log)}>
      <Controller
        name="category"
        control={control}
        rules={{ required: "Selecione uma categoria" }}
        render={({ field, fieldState }) => (
          <div>
            <CustomSelect
              value={field.value}
              onValueChange={field.onChange}
              options={["Eletronicos", "Roupas", "Casa"]}
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
const { register, watch, formState: { errors } } = useForm<SignUpFormData>({
  resolver: zodResolver(signUpSchema),
  mode: "onChange",        // valida ao digitar
  // mode: "onBlur",      // valida ao sair do campo
  // mode: "onTouched",   // valida ao sair do campo, mas so depois do primeiro toque
})

// Indicador de forca de senha
const password = watch("password", "")

function PasswordStrengthIndicator({ password }: { password: string }) {
  const strength = calculatePasswordStrength(password) // 0-4

  const colors = ["bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-lime-500", "bg-green-500"]
  const labels = ["Muito fraca", "Fraca", "Media", "Forte", "Muito forte"]

  return (
    <div className="space-y-1">
      <div className="flex gap-1">
        {[0, 1, 2, 3].map((barIndex) => (
          <div key={barIndex} className={`h-1.5 flex-1 rounded-full transition-colors ${
            barIndex <= strength ? colors[strength] : "bg-gray-200"
          }`} />
        ))}
      </div>
      {password && <p className="text-xs text-gray-500">{labels[strength]}</p>}
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
const personalDataStepSchema = z.object({
  name: z.string().trim().min(2).max(100),
  email: z.string().trim().email().max(254),
})
const addressStepSchema = z.object({
  address: z.string().trim().min(5).max(200),
  city: z.string().trim().min(2).max(100),
})
// Cartao: na pratica use o componente do gateway (Stripe Elements) — o numero nunca passa pelo seu servidor
const paymentStepSchema = z.object({ cardNumber: z.string().regex(/^\d{13,19}$/, "Numero de cartao invalido") })

const stepSchemas = [personalDataStepSchema, addressStepSchema, paymentStepSchema]
const totalSteps = stepSchemas.length

function MultiStepForm() {
  const [currentStep, setCurrentStep] = useState(0)

  const formMethods = useForm({
    resolver: zodResolver(stepSchemas[currentStep]),
    mode: "onBlur",
  })

  async function goToNextStep() {
    const isStepValid = await formMethods.trigger()
    if (!isStepValid) return
    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      // Ultima etapa — enviar
      formMethods.handleSubmit(submitForm)()
    }
  }

  function goToPreviousStep() {
    if (currentStep > 0) setCurrentStep(currentStep - 1)
  }

  return (
    <FormProvider {...formMethods}>
      {/* Indicador de progresso */}
      <div className="flex gap-2 mb-6">
        {stepSchemas.map((_, stepIndex) => (
          <div key={stepIndex} className={`h-2 flex-1 rounded-full transition-colors ${
            stepIndex <= currentStep ? "bg-blue-600" : "bg-gray-200"
          }`} />
        ))}
      </div>

      <form onSubmit={(event) => event.preventDefault()}>
        {currentStep === 0 && <PersonalDataStep />}
        {currentStep === 1 && <AddressStep />}
        {currentStep === 2 && <PaymentStep />}

        <div className="flex justify-between mt-6">
          {currentStep > 0 && (
            <button type="button" onClick={goToPreviousStep}
              className="px-4 py-2 text-gray-600 hover:text-gray-800">
              Voltar
            </button>
          )}
          <button type="button" onClick={goToNextStep}
            className="ml-auto px-6 py-2 bg-blue-600 text-white rounded-lg">
            {currentStep === totalSteps - 1 ? "Finalizar" : "Proximo"}
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
const uploadSchema = z.object({
  file: z
    .instanceof(FileList)
    .refine((fileList) => fileList.length > 0, "Selecione um arquivo")
    .refine((fileList) => fileList[0]?.size <= 5_000_000, "Arquivo deve ter no maximo 5MB")
    .refine(
      (fileList) => ["image/jpeg", "image/png", "image/webp"].includes(fileList[0]?.type),
      "Formato aceito: JPG, PNG ou WebP"
    ),
})

function ImageUploadField() {
  const { register, watch, formState: { errors } } = useForm({
    resolver: zodResolver(uploadSchema),
  })

  const file = watch("file")
  const previewUrl = file?.[0] ? URL.createObjectURL(file[0]) : null

  return (
    <div>
      <label className="
        flex flex-col items-center justify-center w-full h-48
        border-2 border-dashed border-gray-300 rounded-lg
        cursor-pointer hover:border-blue-500 hover:bg-blue-50
        transition-colors
      ">
        {previewUrl ? (
          <img src={previewUrl} alt="Previa" className="h-full object-contain rounded" />
        ) : (
          <>
            <UploadIcon className="h-10 w-10 text-gray-400" />
            <p className="text-sm text-gray-500 mt-2">Clique para enviar imagem</p>
            <p className="text-xs text-gray-400">JPG, PNG ou WebP (max 5MB)</p>
          </>
        )}
        <input type="file" accept="image/*" className="hidden" {...register("file")} />
      </label>
      {errors.file && (
        <p className="text-sm text-red-600 mt-1">{errors.file.message as string}</p>
      )}
    </div>
  )
}
```

---

## 7. Error Display Patterns

```tsx
// INLINE — ao lado do campo (melhor para formularios curtos)
<TextField label="Email" error={errors.email?.message} {...register("email")} />

// TOAST — notificacao flutuante (melhor para erros de servidor)
import { toast } from "sonner" // ou react-hot-toast

async function onSubmit(formData: SignUpFormData) {
  try {
    const response = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
    })
    // fetch NAO lanca erro em 4xx/5xx — conferir response.ok e ler o formato unico (D13)
    if (!response.ok) {
      const { error } = await response.json()
      toast.error(error?.message ?? "Erro ao criar conta. Tente novamente.")
      return
    }
    toast.success("Conta criada com sucesso!")
  } catch {
    toast.error("Erro ao criar conta. Tente novamente.")
  }
}

// SUMMARY — resumo no topo do form (melhor para formularios longos)
function ErrorSummary({ errors }: { errors: Record<string, { message?: string }> }) {
  const errorList = Object.entries(errors).filter(([, fieldError]) => fieldError.message)
  if (errorList.length === 0) return null

  return (
    <div role="alert" className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
      <p className="font-medium text-red-800">Corrija os erros abaixo:</p>
      <ul className="mt-2 list-disc list-inside text-sm text-red-600">
        {errorList.map(([fieldName, error]) => (
          <li key={fieldName}>{error.message}</li>
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
      const firstInvalidField = formRef.current.querySelector<HTMLInputElement>(
        '[aria-invalid="true"]'
      )
      firstInvalidField?.focus()
    }
  }, [errors])

  return formRef
}

// Campo acessivel completo
<div role="group" aria-labelledby="contact-group">
  <h3 id="contact-group" className="text-lg font-semibold mb-2">Dados de Contato</h3>
  <input
    id="email"
    type="email"
    aria-label="Endereco de email"
    aria-required="true"
    aria-invalid={!!errors.email}
    aria-describedby={errors.email ? "email-error" : "email-help"}
    {...register("email")}
  />
  <p id="email-help" className="text-xs text-gray-500">Usaremos para enviar a confirmacao</p>
  {errors.email && <p id="email-error" role="alert" className="text-sm text-red-600">{errors.email.message}</p>}
</div>
```

---

## 9. Optimistic UI

```tsx
"use client"
import { useState } from "react"

function CommentForm({ postId }: { postId: string }) {
  const [comments, setComments] = useState<Comment[]>([])
  const { register, handleSubmit, reset } = useForm()

  async function onSubmit(formData: { text: string }) {
    // 1. Adiciona IMEDIATAMENTE na lista (otimista)
    const temporaryComment: Comment = {
      id: `temp-${Date.now()}`,
      text: formData.text,
      author: "Voce",
      status: "sending",
    }
    setComments((previousComments) => [...previousComments, temporaryComment])
    reset()

    try {
      // 2. Envia para o servidor
      const response = await fetch("/api/comments", {
        method: "POST",
        body: JSON.stringify({ postId, text: formData.text }),
      })
      const savedComment = await response.json()

      // 3. Substitui o temporario pelo real
      setComments((previousComments) =>
        previousComments.map((comment) => (comment.id === temporaryComment.id ? savedComment : comment))
      )
    } catch {
      // 4. Se falhou, marca como erro (usuario pode tentar de novo)
      setComments((previousComments) =>
        previousComments.map((comment) =>
          comment.id === temporaryComment.id ? { ...comment, status: "error" } : comment
        )
      )
    }
  }

  return (
    <div>
      <ul className="space-y-2 mb-4">
        {comments.map((comment) => (
          <li key={comment.id} className={comment.status === "sending" ? "opacity-50" : ""}>
            <span>{comment.text}</span>
            {comment.status === "error" && (
              <button className="text-red-500 text-xs ml-2">Tentar novamente</button>
            )}
          </li>
        ))}
      </ul>
      <form onSubmit={handleSubmit(onSubmit)} className="flex gap-2">
        <input {...register("text")} placeholder="Escreva um comentario..."
          className="flex-1 px-4 py-2 border rounded-lg" />
        <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">
          Enviar
        </button>
      </form>
    </div>
  )
}
```
