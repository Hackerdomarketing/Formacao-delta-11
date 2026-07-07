# Monitoramento de Erros em Produção

> Endereço canônico desta integração (Regra Inviolável 15): a pasta é nomeada pela FUNÇÃO no produto
> (monitoramento de erros), nunca pelo vendor. Se o vendor mudar, este README muda — o endereço não.

- **Função no produto:** capturar todo erro que acontece na mão do usuário real em produção, com a linha exata do código, o usuário afetado e o caminho até o erro.
- **Vendor atual:** Sentry (plano gratuito atende projetos iniciais — ~5 mil erros/mês)
- **Status:** ⬜ não instalado ainda | ⬜ instalado e testado (SHIELD bloqueia deploy de produção sem o teste)

## Instalação (ENGINE/BACK, quando o projeto caminhar para produção)

```bash
npx @sentry/wizard@latest -i nextjs
```

O assistente oficial cria as configurações de cliente, servidor e edge, e adiciona `SENTRY_DSN`/`NEXT_PUBLIC_SENTRY_DSN` — registre os NOMES no `.env.example` (sem valores) e a conta em `.delta-11/memoria/ferramentas-do-projeto.md` (Regra 14, via tool-provisioner).

## Regras de uso

1. **Nunca enviar dado sensível junto com o erro:** configurar `beforeSend` para remover senha, token, dados de cartão (mesma regra de logging do regras-codigo §3).
2. **Adaptador:** o resto do código captura erros por UMA função própria (`captureError(error, context)`) exportada daqui — trocar de vendor no futuro = reescrever 1 arquivo (padrão Adapter, design-patterns-praticos §5).
3. **Teste obrigatório pré-deploy:** disparar um erro proposital e confirmar que apareceu no painel — o SHIELD exige a evidência.
