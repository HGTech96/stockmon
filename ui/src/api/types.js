/**
 * JSDoc type definitions mirroring docs/api-contract.md v1.1 exactly.
 * Documentation only -- no runtime validation. Field names match the
 * contract's camelCase JSON shapes so they can be used as-is on API
 * client return values.
 */

/**
 * @typedef {Object} Meta
 * @property {string} dataAsOf - ISO 8601 timestamp with timezone.
 * @property {boolean} isStale
 * @property {string|null} staleMessage
 */

/**
 * @typedef {Object} ChecklistItem
 * @property {string} id
 * @property {string} text
 * @property {boolean} passed
 */

/**
 * @typedef {Object} Suggestion
 * @property {"BUY"|"WAIT"|"SELL"} label
 * @property {"entry"|"exit"} type
 * @property {number} metCount
 * @property {number} totalCount
 * @property {ChecklistItem[]} checklist
 * @property {string|null} note
 */

/**
 * @typedef {Object} Warning
 * @property {"1d_move"|"7d_move"} reason
 * @property {string} text
 */

/**
 * @typedef {Object} Summary
 * @property {number} totalInvested
 * @property {number} totalCurrentValue
 * @property {number} totalProfitLoss
 * @property {number} totalProfitLossPct
 */

/**
 * @typedef {Object} Money
 * @property {number} cashAvailable
 * @property {number} netDeposited
 * @property {number} realizedEarned
 * @property {number} realizedLost - positive magnitude, not signed
 * @property {number} unrealizedGainOpen
 * @property {number} unrealizedLossOpen - positive magnitude, not signed
 */

/**
 * @typedef {Object} DashboardPosition
 * @property {number} profitLoss
 * @property {number} profitLossPct
 */

/**
 * @typedef {Object} DashboardStock
 * @property {string} ticker
 * @property {string} companyName
 * @property {number} currentPrice
 * @property {number} change1dPct
 * @property {"ok"|"insufficient_history"} status
 * @property {"BUY"|"WAIT"|"SELL"|null} suggestion
 * @property {Warning|null} warning
 * @property {DashboardPosition|null} position
 */

/**
 * @typedef {Object} DashboardResponse
 * @property {Meta} meta
 * @property {Summary|null} summary
 * @property {Money|null} money
 * @property {DashboardStock[]} stocks
 */

/**
 * @typedef {Object} ChartDay
 * @property {string} date - YYYY-MM-DD
 * @property {number} close
 * @property {number} volume
 */

/**
 * @typedef {Object} ChartData
 * @property {ChartDay[]} days
 * @property {number} thirtyDayAverage
 * @property {number|null} userAvgPurchasePrice
 */

/**
 * @typedef {Object} Indicators
 * @property {number} currentPrice
 * @property {number} change1dPct
 * @property {number} change7dPct
 * @property {number} thirtyDayAverage
 * @property {number} thirtyDayHigh
 * @property {number} thirtyDayLow
 * @property {number} distanceFromHighPct
 * @property {number} distanceFromLowPct
 * @property {number} rsi
 * @property {number} todaysVolume
 * @property {number} averageVolume
 * @property {number} volumeVsAveragePct
 */

/**
 * @typedef {Object} ProfitTarget
 * @property {number} targetDollars
 * @property {number} progressDollars
 * @property {number} remainingDollars
 * @property {boolean} reached
 */

/**
 * @typedef {Object} Position
 * @property {number} sharesHeld
 * @property {number} avgPurchasePrice
 * @property {number} amountInvested
 * @property {number} currentValue
 * @property {number} profitLoss
 * @property {number} profitLossPct
 * @property {ProfitTarget} profitTarget
 */

/**
 * @typedef {Object} NewsLinks
 * @property {string} cnnFinance
 * @property {string} yahooFinance
 * @property {string} googleFinance
 * @property {string|null} investorRelations
 */

/**
 * @typedef {Object} StockDetailResponse
 * @property {Meta} meta
 * @property {string} ticker
 * @property {string} companyName
 * @property {number|null} currentPrice
 * @property {number|null} change1dPct
 * @property {"ok"|"insufficient_history"} status
 * @property {number} daysOfHistoryAvailable
 * @property {number} daysOfHistoryRequired
 * @property {number|null} tradingDaysUntilReady
 * @property {Suggestion|null} suggestion
 * @property {Warning|null} warning
 * @property {ChartData|null} chart
 * @property {Indicators|null} indicators
 * @property {Position|null} position
 * @property {NewsLinks} newsLinks
 */

/**
 * @typedef {Object} PortfolioPosition
 * @property {string} ticker
 * @property {string} companyName
 * @property {number} sharesHeld
 * @property {number} avgPurchasePrice
 * @property {number} amountInvested
 * @property {number} currentValue
 * @property {number} profitLoss
 * @property {number} profitLossPct
 * @property {ProfitTarget} profitTarget
 * @property {"ok"|"insufficient_history"} status
 * @property {"BUY"|"WAIT"|"SELL"|null} suggestion
 */

/**
 * @typedef {Object} PortfolioResponse
 * @property {Meta} meta
 * @property {boolean} hasTrades
 * @property {Summary|null} summary
 * @property {Money|null} money
 * @property {PortfolioPosition[]} positions
 * @property {string[]} watchlist
 */

/**
 * @typedef {Object} TradeRequest
 * @property {string} ticker
 * @property {"buy"|"sell"} action
 * @property {number} shares
 * @property {number} pricePerShare
 * @property {string} date - YYYY-MM-DD
 */

/**
 * @typedef {Object} Trade
 * @property {number} id
 * @property {string} ticker
 * @property {"buy"|"sell"} action
 * @property {number} shares
 * @property {number} pricePerShare
 * @property {string} date
 */

/**
 * @typedef {Object} UpdatedPosition
 * @property {string} ticker
 * @property {number} sharesHeld
 * @property {number} avgPurchasePrice
 * @property {number} amountInvested
 */

/**
 * @typedef {Object} TradeResponse
 * @property {Trade} trade
 * @property {UpdatedPosition|null} updatedPosition
 */

/**
 * @typedef {Object} TradeHistoryEntry
 * @property {number} id
 * @property {string} ticker
 * @property {string} companyName
 * @property {"buy"|"sell"} action
 * @property {number} shares
 * @property {number} pricePerShare
 * @property {number} totalUsd
 * @property {number|null} realizedPnlUsd
 * @property {string} date - YYYY-MM-DD
 */

/**
 * @typedef {Object} TradesResponse
 * @property {Meta} meta
 * @property {TradeHistoryEntry[]} trades
 */

/**
 * @typedef {Object} TradeUpdateRequest
 * @property {number} shares
 * @property {number} pricePerShare
 * @property {string} date - YYYY-MM-DD
 */

/**
 * @typedef {Object} RefreshFailure
 * @property {string} ticker
 * @property {string} error
 */

/**
 * @typedef {Object} RefreshResponse
 * @property {string[]} refreshed
 * @property {RefreshFailure[]} failed
 * @property {string} dataAsOf
 */

/**
 * @typedef {Object} Settings
 * @property {number} defaultProfitTargetDollars
 * @property {Object<string, number>} perPositionTargets
 */

/**
 * @typedef {Object} CashEventRequest
 * @property {"deposit"|"withdraw"} type
 * @property {number} amountUsd
 * @property {string} date - YYYY-MM-DD
 */

/**
 * @typedef {Object} CashEvent
 * @property {number} id
 * @property {"deposit"|"withdraw"} type
 * @property {number} amountUsd
 * @property {string} date
 */

/**
 * @typedef {Object} CashEventResponse
 * @property {CashEvent} event
 * @property {number} cashAvailable
 */

/**
 * @typedef {Object} ApiError
 * @property {string} error
 */

/**
 * @typedef {Object} AddStockResponse
 * @property {string} ticker
 * @property {string} companyName
 * @property {boolean} historyFetched - false when the ticker resolved but
 *   its price history couldn't be fetched immediately (rare); the row
 *   shows "insufficient_history" until the next refresh.
 */

/**
 * @typedef {Object} ScreenerResult
 * @property {string} ticker
 * @property {string} companyName
 * @property {number} currentPrice
 * @property {number} change1dPct
 * @property {"BUY"|"WAIT"|null} suggestion - entry-only, null when insufficient_history
 * @property {number|null} metCount
 * @property {number|null} totalCount
 * @property {number|null} rsi
 * @property {number|null} priceVs30dAvgPct
 * @property {boolean|null} sharpMove
 * @property {"ok"|"insufficient_history"} status
 */

/**
 * @typedef {Object} ScreenerResponse
 * @property {Meta} meta
 * @property {string|null} runAt - ISO 8601 with timezone; null when the screener has never run
 * @property {ScreenerResult[]} results
 */
// GET /api/screener/{ticker}/detail reuses StockDetailResponse as-is (the
// contract specifies an identical shape, position always null).

export {};
