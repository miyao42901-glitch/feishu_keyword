/** 预估消耗大于当前余额时的提示文案 */
export const POINTS_INSUFFICIENT_MSG = '点数不足，请先充值'

/** 客服二维码图片：默认 `public/custom.png`，可由环境变量覆盖 */
export function getCustomerServiceQrUrl(): string {
  return (
    (import.meta.env.VITE_CUSTOMER_SERVICE_QR_URL as string | undefined)?.trim() ||
    `${import.meta.env.BASE_URL}custom.png`
  )
}

/** 预估消耗（上限）是否高于当前积分余额 */
export function isPointsInsufficient(estimatedPoints: number, balancePoints: number): boolean {
  const estimate = Math.floor(estimatedPoints)
  const balance = Math.floor(balancePoints)
  return estimate > 0 && balance < estimate
}
