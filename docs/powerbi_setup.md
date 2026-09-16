# Power BI Connection, Star Schema & Setup Guide

This guide provides end-to-end instructions for connecting **Power BI Desktop** to the PostgreSQL database, configuring the star-schema semantic model, establishing relationships, and configuring scheduled data refreshes.

---

## 1. Prerequisites & Connection Parameters

Ensure PostgreSQL is accessible from the machine running Power BI Desktop.

### Connection Parameters (Template)
| Parameter | Value / Placeholder | Notes |
| :--- | :--- | :--- |
| **Server** | `localhost:5432` or `<YOUR_POSTGRES_HOST>:<PORT>` | Default PostgreSQL port is `5432` |
| **Database** | `stock_portfolio_intelligence` | Standalone analytics project database |
| **Data Connectivity Mode** | **Import** (Recommended) or **DirectQuery** | See mode comparison below |
| **Database Credentials** | User: `<YOUR_POSTGRES_USER>` / Password: `<YOUR_POSTGRES_PASSWORD>` | Entered securely in Power BI credential prompt |

> [!CAUTION]
> Never hardcode or commit database passwords into Power BI template files (`.pbit`) or repository documentation. Use Power BI Desktop's encrypted Windows Credential Manager.

---

## 2. Connecting to PostgreSQL in Power BI Desktop

1. Launch **Power BI Desktop**.
2. On the ribbon, select **Get Data** > **More...** > **Database** > **PostgreSQL database** > **Connect**.
3. In the PostgreSQL connection dialog:
   - **Server**: `localhost:5432`
   - **Database**: `stock_portfolio_intelligence`
   - **Data Connectivity mode**: Select **Import** (recommended for full DAX time-intelligence performance).
4. Click **OK**.
5. When prompted for credentials:
   - Select **Database** tab on the left.
   - Enter your PostgreSQL username and password.
   - Set encryption level to **Encrypted connection** (or Unencrypted for local development if SSL is disabled).
6. In the **Navigator** window, expand the `public` schema.

---

## 3. Selecting the Curated Analytical Views

Import **only** the curated SQL views created in `migrations/002_powerbi_views.sql`. Do not import raw base tables directly:

```
public
├── [x] vw_dim_date                    (Calendar dimension)
├── [x] vw_dim_assets                  (Asset metadata dimension)
├── [x] vw_dim_portfolios              (Portfolio containers & benchmark)
├── [x] vw_fact_portfolio_performance  (Time-series valuation curves)
├── [x] vw_fact_portfolio_holdings     (Current positions & weights)
├── [x] vw_fact_portfolio_trades       (Transaction ledger)
└── [x] vw_fact_portfolio_risk_metrics (Pre-computed factor scorecards)
```

Click **Load** (or **Transform Data** if you wish to inspect column datatypes in Power Query).

---

## 4. Star Schema Semantic Model Configuration

In Power BI Desktop, navigate to **Model View** (left navigation bar) to configure table relationships.

```
                      ┌──────────────────┐
                      │   vw_dim_date    │
                      │  (PK: date)      │
                      └─────────┬────────┘
                                │ 1:N
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│vw_fact_portfolio_ │   │vw_fact_portfolio_ │   │vw_fact_portfolio_ │
│    performance    │   │      trades       │   │   risk_metrics    │
│(FK: snapshot_date)│   │ (FK: trade_date)  │   │  (FK: as_of_date) │
└─────────▲─────────┘   └─────────▲─────────┘   └─────────▲─────────┘
          │                       │                       │
          │ N:1                   │ N:1                   │ N:1
┌─────────┴─────────┐   ┌─────────┴─────────┐   ┌─────────┴─────────┐
│ vw_dim_portfolios │   │   vw_dim_assets   │   │ vw_fact_portfolio_│
│(PK: portfolio_id) │   │   (PK: ticker)    │   │     holdings      │
└───────────────────┘   └───────────────────┘   └───────────────────┘
```

### Explicit Relationship Mappings

| From Fact Table | Foreign Key | To Dimension Table | Primary Key | Cardinality | Cross Filter Direction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `vw_fact_portfolio_performance` | `portfolio_id` | `vw_dim_portfolios` | `portfolio_id` | Many to One (`*:1`) | Single |
| `vw_fact_portfolio_performance` | `snapshot_date` | `vw_dim_date` | `date` | Many to One (`*:1`) | Single |
| `vw_fact_portfolio_holdings` | `portfolio_id` | `vw_dim_portfolios` | `portfolio_id` | Many to One (`*:1`) | Single |
| `vw_fact_portfolio_holdings` | `ticker` | `vw_dim_assets` | `ticker` | Many to One (`*:1`) | Single |
| `vw_fact_portfolio_trades` | `portfolio_id` | `vw_dim_portfolios` | `portfolio_id` | Many to One (`*:1`) | Single |
| `vw_fact_portfolio_trades` | `ticker` | `vw_dim_assets` | `ticker` | Many to One (`*:1`) | Single |
| `vw_fact_portfolio_trades` | `trade_date` | `vw_dim_date` | `date` | Many to One (`*:1`) | Single |
| `vw_fact_portfolio_risk_metrics` | `portfolio_id` | `vw_dim_portfolios` | `portfolio_id` | Many to One (`*:1`) | Single |
| `vw_fact_portfolio_risk_metrics` | `as_of_date` | `vw_dim_date` | `date` | Many to One (`*:1`) | Single |

### Marking Date Table
1. Select table `vw_dim_date` in Model View.
2. In the ribbon, select **Table tools** > **Mark as date table**.
3. Choose column `date` and click **OK**.

---

## 5. DirectQuery vs. Import Mode Recommendations

| Feature | Import Mode (Recommended) | DirectQuery Mode |
| :--- | :--- | :--- |
| **Performance** | In-memory VertiPaq engine delivers sub-second chart rendering and instant slicer response. | Queries PostgreSQL on every click, creating latency for complex matrices. |
| **DAX Capability** | Full support for advanced time-intelligence (`TOTALYTD`, `LASTNONBLANKVALUE`). | Limited DAX function set; complex measures may fail or be restricted. |
| **Data Freshness** | Refreshes on schedule (e.g. daily after market close). | Real-time live data directly against PostgreSQL. |
| **Recommendation** | **Best for portfolio reporting & presentations.** | Only necessary if real-time intraday tick streaming is required. |

---

## 6. Scheduled Refresh & Gateway Configuration

When publishing to **Power BI Service** (cloud):

1. **On-Premises Data Gateway**:
   - Install the **Power BI On-Premises Data Gateway** (Standard Mode) on the server hosting PostgreSQL.
   - Register the gateway with your Power BI Service tenant.
2. **Dataset Credentials**:
   - In Power BI Service, navigate to **Dataset Settings** > **Gateway connection**.
   - Map the data source `PostgreSQL localhost:5432 stock_portfolio_intelligence` to the gateway.
   - Enter database credentials under **Data source credentials**.
3. **Refresh Schedule**:
   - Configure **Scheduled Refresh** for market close (e.g., 5:00 PM EST / 4:00 PM IST) following the daily market data ingestion pipeline execution.
