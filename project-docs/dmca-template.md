# DMCA Takedown Notice — Template

> 命中水印（`scripts/scan_corpus.py` 反查到 `(page, build_id)`）后，把以下模板发给侵权方所在平台的 DMCA 联络方。
> 各大语料 / 模型平台的 DMCA 入口见文末"提交渠道"。

---

## 模板（英文，平台主流接受语言）

> ```
> Subject: DMCA Takedown Notice — Unauthorized Use of Copyrighted Content from LewisDocs
>
> To Whom It May Concern,
>
> I am the copyright owner (or authorized agent thereof) of original
> research content published at the URL below:
>
>     Original work URL: https://lewisdocs.pages.dev/<PAGE-PATH>
>     Repository:        https://github.com/Lewis0x/LewisDocs
>     License:           CC BY-NC-ND 4.0 + AI Use Restriction Addendum
>                        (full text: https://github.com/Lewis0x/LewisDocs/blob/main/LICENSE)
>
> The infringing material is reproduced at:
>
>     Infringing URL / dataset / model identifier: <INSERT URL OR DATASET ID>
>     Specific location within infringing material: <INSERT EXCERPT OR ROW ID>
>
> Identification of the infringement (verifiable by zero-width-character
> watermark embedded by my publishing pipeline):
>
>     Watermark string (zero-width characters; copy-paste preserves them):
>         <PASTE WATERMARK STRING FROM scan_corpus.py output>
>     Decoded payload (page identifier and build ID):
>         <PASTE PAYLOAD FROM scan_corpus.py output>
>     Build manifest reference (private):
>         File path = <FROM MANIFEST>
>         Build ID  = <FROM MANIFEST>
>
> The use of this content for the purposes of (check whichever applies):
>     [ ] LLM pre-training / fine-tuning / RLHF / distillation
>     [ ] Embedding generation for retrieval-augmented generation (RAG)
>     [ ] Synthetic-data or alignment-dataset construction
>     [ ] Bulk redistribution / commercial scraping
>     [ ] Other: <DESCRIBE>
>
> is expressly prohibited under the AI Use Restriction Addendum to the
> license attached. No permission has been granted by the copyright holder.
>
> I have a good-faith belief that use of the material in the manner
> complained of is not authorized by the copyright owner, its agent, or
> the law.
>
> The information in this notification is accurate, and under penalty of
> perjury, I am the owner of an exclusive right that is allegedly infringed.
>
> I request that you remove or disable access to the infringing material.
>
> Signed,
> <YOUR LEGAL NAME>
> <YOUR ROLE / TITLE>
> <CONTACT EMAIL>
> <PHYSICAL ADDRESS — required by 17 U.S.C. § 512(c)(3)(A)(iv)>
> <DATE>
> ```

---

## 提交渠道

| 平台 | 入口 |
|---|---|
| Hugging Face datasets / models | https://huggingface.co/legal/content-guidelines + DMCA email `legal@huggingface.co` |
| Common Crawl | https://commoncrawl.org/dmca/ + email `info@commoncrawl.org` |
| OpenAI（如内容出现在 ChatGPT 输出） | https://openai.com/policies/dmca-policy + email `dmca@openai.com` |
| Anthropic | https://www.anthropic.com/legal + email `legal@anthropic.com` |
| Google | https://reportcontent.google.com/troubleshooter |
| GitHub（如出现在 repo） | https://docs.github.com/en/site-policy/content-removal-policies/dmca-takedown-policy |
| Cloudflare（如内容由 CF 托管） | https://www.cloudflare.com/abuse/form |
| Internet Archive | https://help.archive.org/help/rights/ |

## 提交清单

- [ ] 已用 `scan_corpus.py` 命中水印并导出证据
- [ ] 已截图 / 归档侵权页面（用 Wayback Machine 锁定时间戳）
- [ ] 已下载 / 备份原始证据（避免对方删除后取证困难）
- [ ] 模板填好，签名 + 实名 + 通讯地址（DMCA 法律要求）
- [ ] 通过该平台官方 DMCA 渠道提交（不要发给客服 / 一般 abuse）
- [ ] 抄送 `Cloudflare CSAM/Abuse` 如果对方域名在 CF 上
- [ ] 在 `project-docs/` 加 `dmca-cases/<date>-<target>.md` 留档

## 结案后

- 在 `_watermark-manifest.json` 对应条目加 note：`"breached": true, "case": "<date>-<target>"`
- 如该 build 的 manifest 已多次被泄漏，触发**水印轮换**：发布一次空 commit 触发 CI，让所有页面拿新 build_id 的水印（旧水印仍有取证价值，新水印用于追未来泄漏）
