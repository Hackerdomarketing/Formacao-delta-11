# ARQUITETURA DE CÓDIGO POR PLATAFORMA — Formação Δ-11

> **Quem lê este arquivo:** ATLAS (durante planejamento de qualquer projeto) e agentes de código quando precisam saber a estrutura correta para a plataforma do projeto.
>
> **Quando usar:** Sempre que o projeto NÃO for web (Next.js). Para projetos web, a estrutura padrão já está no ATLAS. Para Windows, iOS, Android, Flutter, React Native ou extensão de navegador, consulte a seção correspondente abaixo.

---

## Como usar este protocolo

O ATLAS lê este arquivo na **Fase 2 (Arquitetura)** ao criar o `project-core.md`. No bloco `DECISÕES TÉCNICAS CRÍTICAS` do project-core.md, ATLAS inclui:
- A plataforma do projeto
- A estrutura de pastas adotada (copiada daqui)
- As nomenclaturas padrão da plataforma
- O padrão de arquitetura escolhido (MVVM, Clean Architecture, etc.)

Os agentes de código (ENGINE, FRONT, PIXEL) consultam o `project-core.md` — que já terá essas decisões registradas.

### Regra de tamanho de projeto

| Tamanho | Critério | Padrão de arquitetura |
|---------|----------|----------------------|
| Pequeno | 1-3 devs, poucas telas | MVVM simples |
| Médio | 3-10 devs, muitas telas | MVVM + Feature-Based |
| Grande | 10+ devs, múltiplos módulos | Clean Architecture + Feature-Based |

---

## 1. SOFTWARE DESKTOP WINDOWS (C# / .NET)

**Stack:** C# + WPF (complexo) ou WinUI 3 (moderno) + SQLite (local) + MVVM

### Estrutura de pastas

```
MeuApp/
├── MeuApp.sln
├── src/
│   ├── MeuApp.Core/                    ← Lógica de negócio (não depende de UI)
│   │   ├── Models/                     ← Classes de dados
│   │   ├── Services/                   ← Lógica (IUserService.cs + UserService.cs)
│   │   ├── Interfaces/                 ← Contratos compartilhados
│   │   └── Exceptions/
│   ├── MeuApp.Infrastructure/          ← Acesso a dados e APIs externas
│   │   ├── Data/
│   │   │   ├── AppDbContext.cs
│   │   │   ├── Repositories/
│   │   │   └── Migrations/
│   │   └── ExternalServices/
│   └── MeuApp.UI/                      ← Interface (WPF/WinUI)
│       ├── App.xaml
│       ├── Views/                      ← Telas/janelas (.xaml)
│       ├── ViewModels/                 ← Lógica da UI (binding)
│       ├── Converters/
│       ├── Resources/
│       └── Controls/
├── tests/
│   ├── MeuApp.Core.Tests/
│   └── MeuApp.UI.Tests/
└── docs/
```

### Hierarquia de dependências

```
UI → Core ← Infrastructure
```
- **Core** não depende de nada (é o centro)
- **UI** usa Core (modelos e serviços)
- **Infrastructure** implementa interfaces do Core
- **UI NUNCA depende diretamente de Infrastructure**

### Nomenclaturas (C#)

| Elemento | Convenção | Exemplo |
|----------|-----------|---------|
| Namespace | PascalCase com ponto | `MeuApp.Core.Services` |
| Classe | PascalCase, substantivo | `UserService` |
| Interface | PascalCase com prefixo `I` | `IUserService` |
| Método | PascalCase, verbo | `GetUser()`, `SaveProduct()` |
| Propriedade | PascalCase | `FirstName`, `IsActive` |
| Variável local | camelCase | `userName` |
| Campo privado | `_camelCase` (underscore) | `_userService` |
| Constante | PascalCase ou UPPER_CASE | `MaxRetryCount` |
| Arquivo | Mesmo nome da classe | `UserService.cs` |

---

## 2. SOFTWARE DESKTOP macOS / APP iOS (Swift)

**Stack:** Swift + SwiftUI (novo) ou AppKit (legado macOS) + Core Data / SwiftData + MVVM

### Estrutura de pastas

```
MeuApp/
├── MeuApp.xcodeproj
├── MeuApp/
│   ├── App/
│   │   ├── MeuAppApp.swift             ← Ponto de entrada
│   │   └── ContentView.swift
│   ├── Models/                         ← Dados puros
│   ├── ViewModels/                     ← Lógica das telas
│   ├── Views/                          ← Telas e componentes
│   │   ├── UserList/
│   │   │   ├── UserListView.swift
│   │   │   └── UserRowView.swift
│   │   └── Components/                 ← Componentes reutilizáveis
│   │       ├── LoadingView.swift
│   │       └── ErrorView.swift
│   ├── Services/                       ← APIs e lógica de negócio
│   ├── Networking/                     ← APIClient, Endpoints, NetworkError
│   ├── Utilities/                      ← Extensions e helpers
│   ├── Resources/                      ← Assets.xcassets, Localizable.strings
│   └── Configuration/                  ← AppConfiguration.swift, Info.plist
├── MeuAppTests/
├── MeuAppUITests/
└── Packages/                           ← Swift Package Manager
```

### Nomenclaturas (Swift)

| Elemento | Convenção | Exemplo |
|----------|-----------|---------|
| Arquivo | PascalCase, mesmo nome do tipo | `UserListView.swift` |
| Struct/Class | PascalCase | `UserProfile` |
| Protocolo | PascalCase, adjetivo com "-able" | `Codable`, `Identifiable` |
| Função | camelCase, verbo | `fetchUsers()` |
| Variável | camelCase | `isLoggedIn` |
| Constante | camelCase com `let` | `let maxRetryCount = 3` |
| Enum | PascalCase (tipo), camelCase (casos) | `enum Status { case active }` |
| View | PascalCase + "View" | `UserListView` |
| ViewModel | PascalCase + "ViewModel" | `UserListViewModel` |

---

## 3. APP ANDROID (Kotlin)

**Stack:** Kotlin + Jetpack Compose + Room (SQLite) + Retrofit + Hilt + MVVM + Clean Architecture

### Estrutura de pastas

```
meu-app/
└── app/src/main/java/com/exemplo/meuapp/
    ├── MeuAppApplication.kt
    ├── data/                           ← Camada de Dados
    │   ├── local/
    │   │   ├── AppDatabase.kt
    │   │   ├── dao/                    ← Data Access Objects
    │   │   └── entity/                 ← Entidades do banco
    │   ├── remote/
    │   │   ├── ApiService.kt
    │   │   └── dto/                    ← Data Transfer Objects
    │   └── repository/                 ← Implementação dos repositórios
    ├── domain/                         ← Lógica de Negócio (centro)
    │   ├── model/                      ← Modelos de domínio
    │   ├── repository/                 ← Interfaces (contratos)
    │   └── usecase/                    ← Casos de uso
    ├── presentation/                   ← Camada de UI
    │   ├── navigation/
    │   ├── screens/
    │   │   └── userlist/
    │   │       ├── UserListScreen.kt
    │   │       └── UserListViewModel.kt
    │   ├── components/                 ← Composables reutilizáveis
    │   └── theme/                      ← Color.kt, Theme.kt, Type.kt
    └── di/                             ← Hilt (injeção de dependência)
```

### Hierarquia de dependências (Clean Architecture Android)

```
Presentation → Domain ← Data
```
- **Domain** é o centro, não depende de nada
- **Presentation** depende de Domain (usa UseCases)
- **Data** depende de Domain (implementa interfaces)

### Nomenclaturas (Kotlin)

| Elemento | Convenção | Exemplo |
|----------|-----------|---------|
| Package | minúsculo com ponto | `com.exemplo.meuapp.data` |
| Classe | PascalCase | `UserRepository` |
| Interface | PascalCase (sem `I`) | `UserRepository` (impl: `UserRepositoryImpl`) |
| Função | camelCase | `getUsers()` |
| Constante | `UPPER_SNAKE_CASE` no companion | `const val MAX_RETRY = 3` |
| Composable | PascalCase | `UserListScreen()` |
| ViewModel | PascalCase + "ViewModel" | `UserListViewModel` |
| UseCase | PascalCase + "UseCase" | `GetUsersUseCase` |
| DAO | PascalCase + "Dao" | `UserDao` |
| Entity | PascalCase + "Entity" | `UserEntity` |
| DTO | PascalCase + "Dto" | `UserDto` |

---

## 4. APP CROSS-PLATFORM — Flutter

**Stack:** Flutter + Dart + Provider/Bloc/Riverpod + Feature-Based + Clean Architecture

### Estrutura de pastas

```
meu_app/
├── lib/
│   ├── main.dart
│   ├── app/
│   │   ├── app.dart                    ← Widget raiz
│   │   ├── routes.dart
│   │   └── theme.dart
│   ├── features/                       ← Por funcionalidade
│   │   └── auth/
│   │       ├── data/
│   │       │   ├── models/
│   │       │   ├── repositories/
│   │       │   └── datasources/
│   │       ├── domain/
│   │       │   ├── entities/
│   │       │   ├── repositories/       ← Interfaces
│   │       │   └── usecases/
│   │       └── presentation/
│   │           ├── screens/
│   │           ├── widgets/
│   │           └── providers/
│   ├── core/                           ← Código compartilhado
│   │   ├── constants/
│   │   ├── errors/
│   │   ├── network/
│   │   ├── utils/
│   │   └── widgets/
│   └── config/
│       ├── env.dart
│       └── injection.dart
├── test/
├── assets/
├── pubspec.yaml                        ← Dependências (como package.json)
├── android/
└── ios/
```

### Nomenclaturas (Dart/Flutter)

| Elemento | Convenção | Exemplo |
|----------|-----------|---------|
| Arquivo | snake_case | `user_list_screen.dart` |
| Classe | PascalCase | `UserListScreen` |
| Função | camelCase | `getUsers()` |
| Widget | PascalCase | `UserCard` |
| Diretório | snake_case | `user_list/` |

---

## 5. APP CROSS-PLATFORM — React Native

**Stack:** React Native + TypeScript + React Navigation + Feature-Based

### Estrutura de pastas

```
meu-app/
└── src/
    ├── app/
    │   ├── App.tsx
    │   ├── navigation/
    │   │   ├── AppNavigator.tsx
    │   │   └── AuthNavigator.tsx
    │   └── store/
    ├── features/                       ← Por funcionalidade
    │   └── auth/
    │       ├── screens/
    │       ├── components/
    │       ├── hooks/
    │       ├── services/
    │       └── types.ts
    ├── shared/                         ← Código compartilhado
    │   ├── components/
    │   ├── hooks/
    │   ├── services/
    │   ├── utils/
    │   ├── theme/
    │   └── types/
    └── config/
        ├── api.ts
        └── env.ts
```

Nomenclaturas: igual à seção Web (TypeScript/React) — PascalCase para componentes, camelCase para funções e variáveis.

---

## 6. EXTENSÃO DE NAVEGADOR (Chrome/Firefox)

**Stack:** TypeScript + React (popup complexo) ou Vanilla (simples) + Vite + WebExtensions Manifest V3

### Estrutura de pastas

```
minha-extensao/
├── manifest.json                       ← OBRIGATÓRIO — Manifest V3
├── src/
│   ├── background/                     ← Service Worker (lógica de fundo)
│   │   └── index.ts
│   ├── content/                        ← Injetado nas páginas web
│   │   ├── index.ts
│   │   └── styles.css
│   ├── popup/                          ← Janela do ícone
│   │   ├── index.html
│   │   └── Popup.tsx
│   ├── options/                        ← Página de configurações
│   │   ├── index.html
│   │   └── Options.tsx
│   ├── shared/                         ← Código compartilhado
│   │   ├── storage.ts                  ← Wrapper para chrome.storage
│   │   ├── messaging.ts               ← Comunicação entre partes
│   │   └── types.ts
│   └── assets/                         ← Ícones (16, 48, 128px)
└── dist/                               ← Build final (o que vai para a loja)
```

### Estrutura do manifest.json (Manifest V3)

```json
{
  "manifest_version": 3,
  "name": "Minha Extensão",
  "version": "1.0.0",
  "permissions": ["storage", "tabs", "activeTab"],
  "background": { "service_worker": "dist/background/index.js" },
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["dist/content/index.js"]
  }],
  "action": {
    "default_popup": "dist/popup/index.html",
    "default_icon": { "16": "assets/icon-16.png", "128": "assets/icon-128.png" }
  }
}
```

### Como as partes se comunicam

```
Background (Service Worker)
    ↕ chrome.runtime.sendMessage / onMessage
Content Script (roda na página)
    ↕ chrome.runtime.sendMessage / onMessage
Popup / Options
```

**Regra crítica:** Toda comunicação entre partes da extensão passa por `chrome.runtime.sendMessage`. Content scripts NÃO têm acesso direto ao storage — devem pedir ao background.

---

## 7. APLICAÇÃO WEB FULL-STACK (Next.js — padrão do D-11)

> Esta é a stack padrão para a maioria dos projetos. ATLAS já conhece este padrão. Está aqui para referência completa.

**Stack:** Next.js + TypeScript + Tailwind CSS + Supabase + React Hook Form + Zod + TanStack Query

### Estrutura de pastas (App Router)

```
src/
├── app/                                ← Rotas baseadas em pastas
│   ├── layout.tsx
│   ├── page.tsx                        ← /
│   ├── globals.css
│   ├── (auth)/
│   │   ├── login/page.tsx              ← /login
│   │   └── register/page.tsx           ← /register
│   ├── dashboard/
│   │   ├── layout.tsx
│   │   ├── page.tsx                    ← /dashboard
│   │   └── settings/page.tsx
│   └── api/                            ← API Routes (backend)
│       ├── auth/route.ts
│       ├── users/
│       │   ├── route.ts                ← GET/POST /api/users
│       │   └── [id]/route.ts           ← GET/PUT/DELETE /api/users/:id
│       └── products/route.ts
├── components/
│   ├── ui/                             ← Genéricos: Button, Input, Modal
│   ├── layout/                         ← Header, Sidebar
│   └── features/                       ← Específicos de feature: UserList
├── lib/
│   ├── api.ts                          ← Cliente HTTP configurado
│   ├── auth.ts
│   ├── db.ts                           ← Conexão Supabase
│   └── validations.ts                 ← Schemas Zod
├── hooks/                              ← Hooks customizados
├── services/                           ← Lógica de backend
├── types/                              ← Tipos TypeScript compartilhados
└── utils/                              ← Funções utilitárias
```

### Nomenclaturas (TypeScript/React)

| Elemento | Convenção | Exemplo |
|----------|-----------|---------|
| Arquivo de componente | PascalCase.tsx | `UserList.tsx` |
| Arquivo de utilidade | camelCase.ts | `formatDate.ts` |
| Componente React | PascalCase | `UserList` |
| Hook | camelCase com "use" | `useAuth`, `useProducts` |
| Função | camelCase | `formatDate()` |
| Tipo/Interface | PascalCase | `User`, `ProductResponse` |
| Constante global | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Rota de API | kebab-case na URL | `/api/user-profiles` |

---

## 8. PADRÕES DE ARQUITETURA — Referência Rápida

### MVC
```
View → Controller → Model
```
Usado em: Django, Laravel, Spring MVC. Bom para: apps web server-rendered tradicionais.

### MVVM
```
View ←binding→ ViewModel → Model
```
Usado em: WPF, SwiftUI, Android Jetpack, Vue. Bom para: UI reativa (tela atualiza quando dados mudam).

### Clean Architecture
```
Apresentação → Domínio ← Dados
```
Regra de ouro: **dependências sempre apontam para o centro (domínio)**. Domínio não depende de nada.

### Feature-Based
```
features/
├── auth/     (tudo de auth junto — UI, lógica, dados)
├── products/
└── checkout/
```
Bom para: equipes grandes onde cada time cuida de uma feature.

---

## Fonte

Extraído e adaptado de:
- `pesquisa-ia-programacao/fases/fase-02-arquitetura-por-plataforma.md`
- Fonte: pesquisa interna sobre arquitetura por plataforma
