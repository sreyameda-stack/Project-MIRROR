from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="MIRROR | Retail Intelligence", page_icon="◈", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

.stApp {
    background: #F7F3ED;
    color: #292333;
    font-family: 'DM Sans', sans-serif;
}

/* All text: strong contrast */
p, label, small, span,
[data-testid="stMarkdownContainer"],
[data-testid="stWidgetLabel"],
[data-testid="stCaptionContainer"],
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"] {
    color: #292333 !important;
}

h1, h2, h3, h4 {
    font-family: 'Manrope', sans-serif !important;
    color: #292333 !important;
}

/* Sidebar and guide menu */
[data-testid="stSidebar"] {
    background: #EAE2F2;
    border-right: 1px solid #D9CEE6;
}

[data-testid="stSidebar"] * {
    color: #292333 !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #FFFCF8;
    border: 1px solid #D8CDC4;
    padding: 16px;
    border-radius: 16px;
}

[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
    color: #292333 !important;
    opacity: 1 !important;
}

/* Upload area and expandable menu */
[data-testid="stFileUploader"] *,
[data-testid="stExpander"] summary,
[data-testid="stExpander"] p {
    color: #292333 !important;
}

[data-testid="stExpander"] summary {
    color: #FFFFFF !important;
}

[data-testid="stExpander"] summary svg {
    color: #FFFFFF !important;
}

[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] section,
[data-testid="stFileUploader"] section *,
[data-testid="stFileUploader"] small {
    color: #FFFFFF !important;
}

/* Hero banner */
.mirror-hero {
    background: linear-gradient(
        120deg, #E7DDF5, #F5E7E0 55%, #E3EBDD
    );
    border: 1px solid #D8C9E4;
    padding: 26px 30px;
    border-radius: 22px;
    margin: 8px 0 22px;
}

.mirror-hero p {
    color: #393142 !important;
}

.mirror-eyebrow {
    color: #59436F !important;
    text-transform: uppercase;
    letter-spacing: .14em;
    font-size: .76rem;
    font-weight: 700;
}

/* Dropdowns and input controls */
[data-baseweb="select"] *,
[data-baseweb="input"] *,
[data-baseweb="textarea"] * {
    color: #292333 !important;
}

/* Buttons */
div.stButton > button,
div.stDownloadButton > button {
    border-radius: 11px;
    background: #4A3E59;
    color: #FFFFFF !important;
    border: 1px solid #4A3E59;
    font-weight: 600;
}

div.stButton > button *,
div.stDownloadButton > button * {
    color: #FFFFFF !important;
}

/* Notices */
[data-testid="stAlert"] p {
    color: #292333 !important;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def read_file(file_bytes, filename):
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(BytesIO(file_bytes), low_memory=False)
    if suffix in {".xlsx", ".xls"}:
        # MIRROR's official workbook has a legend in row 1 and column headers in row 2.
        try:
            return pd.read_excel(BytesIO(file_bytes), sheet_name="Order Data", header=1)
        except Exception:
            return pd.read_excel(BytesIO(file_bytes))
    raise ValueError("Please upload a CSV or Excel template.")


def clean_data(frame):
    df = frame.copy()
    df.columns = [str(c).strip().replace("\\n", " ") for c in df.columns]
    df = df.loc[:, ~pd.Index(df.columns).duplicated()]
    df = df.dropna(how="all").dropna(axis=1, how="all")
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)
        df[col] = df[col].replace("", np.nan)
    return df


def guess_col(columns, terms):
    for col in columns:
        name = str(col).lower().replace("_", " ")
        if any(term in name for term in terms):
            return col
    return None


def choose_field(label, columns, guess):
    options = ["(Not selected)"] + list(columns)
    index = options.index(guess) if guess in options else 0
    selected = st.selectbox(label, options, index=index)
    return None if selected == "(Not selected)" else selected


REQUIRED_COLUMNS = [
    "Order_ID", "Customer_ID", "Order_Date", "Total_Order_Value",
    "Product_ID", "Product_Name", "Product_Category", "Quantity",
    "Unit_Price", "Order_Status"
]
OPTIONAL_COLUMNS = [
    "Customer_Name", "Discount_Percentage", "Payment_Method", "Purchase_Channel",
    "Customer_Location", "Customer_Age_Group", "Previous_Purchases",
    "Days_Since_Last_Purchase", "Delivery_Time_Days", "Product_Return_Status",
    "Customer_Feedback", "Satisfaction_Score", "Currency_Code"
]
EXPECTED_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


with st.sidebar:
    st.markdown("## ◈ MIRROR")
    st.caption("RETAIL INTELLIGENCE STUDIO")
    page = st.radio("WORKSPACE", ["Overview", "Explore data", "Retail analytics", "Decision Lab", "Data quality"])
    st.divider()
    st.caption("Use the official MIRROR Order Data template.")

st.markdown("""
<div class="mirror-hero">
<div class="mirror-eyebrow">Consumer behaviour · Product intelligence</div>
<h1>See your retail data differently.</h1>
<p>Download the MIRROR template, add your order history, upload it, and turn your data into useful business decisions.</p>
</div>
""", unsafe_allow_html=True)

# The official workbook is bundled beside this app file so the download works
# locally and after deployment (provided both files are included in the project).
template_file = Path(__file__).with_name("MIRROR_Template.xlsx")
if template_file.exists():
    template_bytes = template_file.read_bytes()
    download_col, guide_col = st.columns([1, 2])
    with download_col:
        st.download_button(
            label="⬇ Download MIRROR Data Template",
            data=template_bytes,
            file_name="MIRROR_Data_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="Download the official 23-column workbook, complete it, and upload it below."
        )
    with guide_col:
        st.info("Start here: download the workbook, fill the purple mandatory columns and any optional fields you have, then upload the completed file below. Keep the sheet name and column headers unchanged.")
else:
    st.error("The MIRROR template workbook is missing. Place MIRROR_Template.xlsx in the same folder as this app file to enable downloads.")

with st.expander("Upload your completed MIRROR template", expanded=("mirror_data" not in st.session_state)):
    st.markdown("Upload one or more completed MIRROR templates. Files are combined as order records; they are not joined as separate database tables.")
    uploads = st.file_uploader(
        "Choose completed MIRROR Excel templates or template-format CSV files",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True,
        help="Use the official MIRROR template and keep its column headers unchanged."
    )

    if uploads:
        st.caption(f"{len(uploads)} file(s) selected")
        loaded_frames = {}
        load_issues = []

        for uploaded_file in uploads:
            try:
                part = clean_data(read_file(uploaded_file.getvalue(), uploaded_file.name))
                missing_required = [c for c in REQUIRED_COLUMNS if c not in part.columns]
                if missing_required:
                    load_issues.append(
                        f"{uploaded_file.name}: missing mandatory columns — {', '.join(missing_required)}"
                    )
                    continue

                # Keep the agreed template schema; add absent optional columns as blank.
                for col in OPTIONAL_COLUMNS:
                    if col not in part.columns:
                        part[col] = np.nan

                part = part[EXPECTED_COLUMNS]
                # Mandatory fields must be populated for every submitted order row.
                missing_by_field = part[REQUIRED_COLUMNS].isna().sum()
                invalid_fields = missing_by_field[missing_by_field > 0]
                if not invalid_fields.empty:
                    details = ", ".join(f"{field}: {int(count)} blank" for field, count in invalid_fields.items())
                    load_issues.append(
                        f"{uploaded_file.name}: fill all mandatory fields before upload ({details})."
                    )
                    continue

                if part.empty:
                    load_issues.append(f"{uploaded_file.name}: the template contains no order rows.")
                    continue

                part["Source_File"] = uploaded_file.name
                loaded_frames[uploaded_file.name] = part

            except Exception as exc:
                load_issues.append(f"{uploaded_file.name}: could not read file ({exc}).")

        if load_issues:
            for issue in load_issues:
                st.warning(issue)

        if loaded_frames:
            if st.button("Load and analyse uploaded orders", type="primary"):
                combined = pd.concat(list(loaded_frames.values()), ignore_index=True)
                # Convert template fields to appropriate types.
                combined["Order_Date"] = pd.to_datetime(combined["Order_Date"], errors="coerce")
                numeric_fields = [
                    "Total_Order_Value", "Quantity", "Unit_Price", "Discount_Percentage",
                    "Previous_Purchases", "Days_Since_Last_Purchase", "Delivery_Time_Days",
                    "Satisfaction_Score"
                ]
                for col in numeric_fields:
                    combined[col] = pd.to_numeric(combined[col], errors="coerce")

                # Keep all rows, but flag duplicate order IDs for review rather than silently dropping them.
                st.session_state["mirror_data"] = combined
                st.session_state["mirror_filename"] = ", ".join(loaded_frames.keys())
                st.session_state["mirror_file_count"] = len(loaded_frames)
                st.session_state["mirror_integration_notes"] = []
                st.session_state["mirror_loaded_issues"] = load_issues
                duplicate_order_ids = int(combined["Order_ID"].duplicated(keep=False).sum())
                if duplicate_order_ids:
                    st.warning(
                        f"{duplicate_order_ids:,} rows have an Order_ID that appears more than once. "
                        "Because this template uses one row per order, check whether the same orders "
                        "were uploaded in more than one file. MIRROR has kept the rows for your review."
                    )
                st.success(
                    f"Loaded {len(loaded_frames)} valid file(s) containing "
                    f"{len(combined):,} order rows."
                )

df = st.session_state.get("mirror_data")
filename = st.session_state.get("mirror_filename", "Uploaded MIRROR template")

if df is None:
    st.info("Download and complete the MIRROR Order Data Template, then upload it here to activate analysis.")
    st.markdown("**Mandatory columns:** " + ", ".join(REQUIRED_COLUMNS))
    a, b, c = st.columns(3)
    a.markdown("### 🛍️ Product intelligence\nCompare products, categories, units and order value.")
    b.markdown("### 👥 Customer intelligence\nUnderstand repeat purchasing and customer segments.")
    c.markdown("### ✦ Decision Lab\nTranslate evidence into practical business actions.")
    st.stop()

st.caption(f"Current dataset: **{filename}** · {len(df):,} order rows · {len(df.columns)} columns")
if st.session_state.get("mirror_file_count", 1) > 1:
    st.caption(f"Combined from {st.session_state['mirror_file_count']} completed template files.")
if st.session_state.get("mirror_loaded_issues"):
    with st.expander("Files that need attention"):
        for issue in st.session_state["mirror_loaded_issues"]:
            st.write("• " + issue)

if page == "Overview":
    st.subheader("Your dataset at a glance")
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    date_cols = [c for c in df.columns if any(t in str(c).lower() for t in ["date", "time", "timestamp"])]
    a, b, c, d = st.columns(4)
    a.metric("Rows", f"{len(df):,}")
    b.metric("Columns", f"{len(df.columns):,}")
    c.metric("Numeric fields", len(numeric_cols))
    d.metric("Potential date fields", len(date_cols))
    st.markdown("### Data preview")
    st.dataframe(df.head(100), use_container_width=True, hide_index=True)
    info = pd.DataFrame({"Column": df.columns.astype(str),
                         "Data type": [str(df[c].dtype) for c in df.columns],
                         "Non-missing": [int(df[c].notna().sum()) for c in df.columns],
                         "Unique": [int(df[c].nunique(dropna=True)) for c in df.columns]})
    st.markdown("### Field guide")
    st.dataframe(info, use_container_width=True, hide_index=True)

elif page == "Explore data":
    st.subheader("Explore a relationship")
    left, right = st.columns(2)
    with left:
        x = st.selectbox("Category / X-axis", df.columns)
    with right:
        numeric = df.select_dtypes(include=np.number).columns.tolist()
        y = st.selectbox("Numeric measure / Y-axis", numeric) if numeric else None
    if y:
        chart_type = st.selectbox("Chart style", ["Bar chart", "Line chart", "Scatter plot"])
        if chart_type == "Scatter plot" and x in numeric:
            chart_df = df[[x, y]].dropna().head(5000)
            fig = px.scatter(chart_df, x=x, y=y, title=f"{y} vs {x}")
        else:
            if chart_type == "Scatter plot":
                st.info("Scatter plots need a numeric X-axis; showing a bar chart instead.")
            grouped = df.groupby(x, dropna=False)[y].agg(["sum", "mean", "count"]).reset_index()
            grouped = grouped.sort_values("sum", ascending=False, na_position="last").head(30)
            if chart_type == "Line chart":
                fig = px.line(grouped, x=x, y="sum", markers=True, title=f"Total {y} by {x}")
            else:
                fig = px.bar(grouped, x=x, y="sum", title=f"Total {y} by {x}")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(grouped if chart_type != "Scatter plot" or x not in numeric else chart_df,
                     use_container_width=True, hide_index=True)
    else:
        st.warning("No numeric fields found. Use Overview or Data quality to inspect this dataset.")

elif page == "Retail analytics":
    st.subheader("Retail & e-commerce analysis")
    cols = df.columns.tolist()
    p, c, e = st.columns(3)
    with p:
        product = choose_field("Product field", cols, "Product_Name" if "Product_Name" in cols else guess_col(cols, ["product", "itemid", "item id", "sku"]))
    with c:
        customer = choose_field("Customer / visitor field", cols, "Customer_ID" if "Customer_ID" in cols else guess_col(cols, ["customer", "visitorid", "visitor id", "user id", "userid"]))
    with e:
        event = choose_field("Event / action field", cols, guess_col(cols, ["event", "action", "interaction"]))
    s, q, t = st.columns(3)
    with s:
        sales = choose_field("Sales / value field", cols, "Total_Order_Value" if "Total_Order_Value" in cols else guess_col(cols, ["revenue", "sales", "amount", "price", "total", "gmv"]))
    with q:
        quantity = choose_field("Quantity field", cols, "Quantity" if "Quantity" in cols else guess_col(cols, ["quantity", "units", "qty"]))
    with t:
        date = choose_field("Date / time field", cols, "Order_Date" if "Order_Date" in cols else guess_col(cols, ["timestamp", "datetime", "date", "time"]))

    for col in [sales, quantity]:
        if col:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    a, b, c, d = st.columns(4)
    a.metric("Rows analysed", f"{len(df):,}")
    b.metric("Unique products", f"{df[product].nunique():,}" if product else "—")
    c.metric("Unique shoppers", f"{df[customer].nunique():,}" if customer else "—")
    d.metric(f"Total {sales}", f"{df[sales].sum(min_count=1):,.2f}" if sales else (f"{df[event].nunique():,} event types" if event else "—"))

    if product and sales:
        summary = df.groupby(product, dropna=False)[sales].sum(min_count=1).sort_values(ascending=False).head(15).reset_index()
        summary.columns = ["Product", f"Total {sales}"]
        st.markdown("### Product performance")
        st.plotly_chart(px.bar(summary, x="Product", y=f"Total {sales}", title=f"Top products by {sales}"), use_container_width=True)
        st.dataframe(summary, use_container_width=True, hide_index=True)
    elif product and event:
        subset = df[df[product].isin(df[product].value_counts().head(15).index)]
        summary = subset.groupby([product, event], dropna=False).size().reset_index(name="Records")
        st.markdown("### Product engagement")
        st.plotly_chart(px.bar(summary, x=product, y="Records", color=event, barmode="group"), use_container_width=True)
        st.dataframe(summary, use_container_width=True, hide_index=True)
    else:
        st.info("Select a product field and a sales/value or event field for product-level analytics.")

    if event:
        event_summary = df[event].fillna("Missing").astype(str).value_counts().rename_axis("Event").reset_index(name="Records")
        st.markdown("### Shopper activity")
        st.plotly_chart(px.bar(event_summary, x="Event", y="Records", title="Records by event / action"), use_container_width=True)
        st.dataframe(event_summary, use_container_width=True, hide_index=True)
    if customer:
        activity = df.groupby(customer).size()
        repeats = int((activity > 1).sum())
        a, b = st.columns(2)
        a.metric("Shoppers with multiple records", f"{repeats:,}")
        b.metric("Share of shoppers with multiple records", f"{repeats / max(len(activity), 1) * 100:.1f}%")
        st.caption("Multiple records indicate repeat activity in this file, not necessarily repeat purchases.")
    if date:
        dates = pd.to_datetime(df[date], errors="coerce", unit="ms" if "timestamp" in str(date).lower() else None)
        dated = pd.DataFrame({"Date": dates}).dropna()
        if not dated.empty:
            trend = dated.assign(Period=dated["Date"].dt.date).groupby("Period").size().reset_index(name="Records")
            st.markdown("### Activity over time")
            st.plotly_chart(px.line(trend, x="Period", y="Records", markers=True), use_container_width=True)

    summary = df.describe(include="all").transpose().reset_index(names="Column")
    st.download_button("Download dataset summary", summary.to_csv(index=False).encode("utf-8"),
                       "mirror_dataset_summary.csv", "text/csv")


elif page == "Decision Lab":
    st.subheader("MIRROR Decision Lab")
    st.markdown(
        "Turn the uploaded dataset into **prioritised next steps**. Recommendations are based only "
        "on fields available in your file; forecasts are scenarios, not guarantees."
    )

    cols = df.columns.tolist()
    product = choose_field("Product field", cols, "Product_Name" if "Product_Name" in cols else guess_col(cols, ["product", "itemid", "item id", "sku", "stockcode", "description"]))
    customer = choose_field("Customer / visitor field", cols, "Customer_ID" if "Customer_ID" in cols else guess_col(cols, ["customer", "visitorid", "visitor id", "user id", "userid", "client"]))
    sales = choose_field("Sales / revenue / value field", cols, "Total_Order_Value" if "Total_Order_Value" in cols else guess_col(cols, ["revenue", "sales", "amount", "gmv", "line total", "totalprice"]))
    quantity = choose_field("Quantity / units field", cols, "Quantity" if "Quantity" in cols else guess_col(cols, ["quantity", "units", "qty"]))
    event = choose_field("Event / action field", cols, guess_col(cols, ["event", "action", "interaction", "event_type"]))
    date = choose_field("Date / time field", cols, "Order_Date" if "Order_Date" in cols else guess_col(cols, ["timestamp", "datetime", "date", "time"]))

    numeric_sales = None
    if sales:
        numeric_sales = pd.to_numeric(df[sales], errors="coerce")

    st.markdown("### Customer probability estimates")
    st.info(
        "MIRROR does not ask users to enter purchase probabilities. It first evaluates the uploaded "
        "history. A validated probability of returning requires enough chronological repeat-purchase "
        "examples and a defined prediction window. A probability of buying a specific product also "
        "requires candidate-product outcomes. Until those conditions and model validation are met, "
        "MIRROR reports observed repeat-purchase patterns rather than invented probabilities."
    )
    st.markdown("### 1. What should we prioritise?")
    if product and numeric_sales is not None:
        product_data = pd.DataFrame({
            "Product": df[product].astype("string").fillna("Unknown"),
            "Value": numeric_sales,
        })
        product_data = product_data.dropna(subset=["Value"])
        product_rank = product_data.groupby("Product", dropna=False)["Value"].agg(["sum", "count", "mean"]).reset_index()
        product_rank.columns = ["Product", "Total value", "Rows", "Average row value"]
        product_rank = product_rank.sort_values("Total value", ascending=False)
        if not product_rank.empty:
            top = product_rank.iloc[0]
            total = product_rank["Total value"].sum()
            share = float(top["Total value"] / total) if total else np.nan
            a, b, c = st.columns(3)
            a.metric("Leading product", str(top["Product"])[:30])
            b.metric("Leading product value", f"{top['Total value']:,.2f}")
            c.metric("Share of selected value", f"{share:.1%}" if pd.notna(share) else "—")
            st.plotly_chart(
                px.bar(product_rank.head(12), x="Product", y="Total value",
                       title="Top products by selected value"),
                use_container_width=True
            )
            st.dataframe(product_rank.head(20), use_container_width=True, hide_index=True)
            st.markdown("**Interpretation**")
            if pd.notna(share) and share >= 0.5:
                st.write(
                    f"**Test protecting and promoting {top['Product']}.** It accounts for "
                    f"{share:.1%} of the selected value in this dataset, so performance may depend "
                    "heavily on it. Check stock, margin and availability before increasing promotion."
                )
            else:
                st.write(
                    f"**Start by testing {top['Product']} as a promotion candidate.** It has the "
                    "highest total selected value in the uploaded data. Compare its margin, stock "
                    "and recent trend before committing more budget."
                )
            st.caption("This ranking uses the selected numeric field as supplied. If you selected unit price rather than line revenue, the ranking is not a sales ranking.")
    elif product and event:
        counts = df.groupby(product, dropna=False).size().sort_values(ascending=False).head(15).rename("Records").reset_index()
        counts.columns = ["Product", "Records"]
        st.plotly_chart(px.bar(counts, x="Product", y="Records", title="Most frequently recorded products"), use_container_width=True)
        st.dataframe(counts, use_container_width=True, hide_index=True)
        if not counts.empty:
            st.write(
                f"**Next step:** investigate the most frequently recorded products first. High record counts can mean high interest, "
                "but they do not prove high purchases. Use the event field below to separate views, carts and purchases when those values exist."
            )
    else:
        st.info("Choose a product field plus a numeric sales/value field, or a product field plus an event field, to generate product priorities.")

    st.divider()
    st.markdown("### 2. Which customer group should we target?")
    if customer:
        cust = df.copy()
        cust["_mirror_customer"] = cust[customer].astype("string")
        if numeric_sales is not None:
            cust["_mirror_value"] = numeric_sales
            customer_summary = cust.dropna(subset=["_mirror_customer"]).groupby("_mirror_customer").agg(
                Records=("_mirror_customer", "size"),
                SelectedValue=("_mirror_value", "sum")
            ).reset_index().rename(columns={"_mirror_customer": "Customer"})
            customer_summary["Group"] = np.select(
                [customer_summary["Records"] >= 3, customer_summary["Records"] == 2],
                ["Frequent recorded activity (3+ rows)", "Two recorded rows"],
                default="One recorded row"
            )
            customer_summary = customer_summary.sort_values("SelectedValue", ascending=False)
            st.dataframe(customer_summary.head(20), use_container_width=True, hide_index=True)
            multi = float((customer_summary["Records"] > 1).mean()) if len(customer_summary) else 0
            st.write(
                f"**Interpretation:** {multi:.1%} of identified customers have multiple rows in this dataset. "
                "That indicates repeated records, not necessarily repeat purchases. If rows are transactions, "
                "use an order/invoice ID to confirm repeat buying before launching a loyalty campaign."
            )
            if len(customer_summary):
                st.write(
                    "**Suggested test:** compare a small re-engagement or loyalty message for customers with "
                    "multiple recorded interactions against a similar group that does not receive it. Measure "
                    "incremental purchases, not just opens or clicks."
                )
        else:
            counts = cust.dropna(subset=["_mirror_customer"]).groupby("_mirror_customer").size().sort_values(ascending=False)
            st.metric("Unique identified customers / visitors", f"{len(counts):,}")
            st.metric("With multiple recorded rows", f"{int((counts > 1).sum()):,}")
            st.write(
                "**Suggested next step:** use repeated activity to form a test group, but don't label these people "
                "as loyal buyers unless the data includes purchase or order information."
            )
    else:
        st.info("Select a customer or visitor ID field to explore customer groups. Avoid uploading names, emails or phone numbers.")

    if event:
        st.markdown("#### Activity signals")
        event_counts = df[event].fillna("Missing").astype(str).value_counts().rename_axis("Event").reset_index(name="Records")
        st.dataframe(event_counts, use_container_width=True, hide_index=True)
        normalized = {str(v).strip().lower().replace(" ", "").replace("_", ""): v for v in event_counts["Event"]}
        view_key = next((k for k in normalized if "view" in k or "click" in k), None)
        cart_key = next((k for k in normalized if "cart" in k or "basket" in k), None)
        purchase_key = next((k for k in normalized if "purchase" in k or "transaction" in k or "checkout" in k), None)
        if view_key and cart_key and purchase_key:
            total_by_event = event_counts.set_index("Event")["Records"].to_dict()
            views = int(total_by_event.get(normalized[view_key], 0))
            carts = int(total_by_event.get(normalized[cart_key], 0))
            purchases = int(total_by_event.get(normalized[purchase_key], 0))
            st.write(
                f"Detected event counts: **{views:,} view-like**, **{carts:,} cart-like**, and "
                f"**{purchases:,} purchase-like** records. These are event counts, not necessarily unique people "
                "or a validated conversion funnel."
            )
            if views > 0:
                st.write(f"View-to-cart event ratio: **{carts / views:.1%}**. Treat this as a directional signal only.")
            st.caption("For a reliable funnel, deduplicate at the visitor/session level and confirm that the event definitions match.")

    st.divider()
    st.markdown("### 3. What could the business growth look like?")
    st.caption("Scenario calculator: choose an assumed uplift to see a simple value illustration. It is not a forecast and does not account for costs or profit.")
    if numeric_sales is not None:
        base_value = float(numeric_sales.dropna().sum())
        if base_value >= 0:
            uplift = st.slider("Assumed improvement in the selected value", min_value=0, max_value=30, value=5, step=1, format="%d%%")
            extra = base_value * uplift / 100
            g1, g2, g3 = st.columns(3)
            g1.metric("Current selected total", f"{base_value:,.2f}")
            g2.metric("Illustrative uplift", f"{extra:,.2f}", f"+{uplift}% assumption")
            g3.metric("Illustrative total", f"{base_value + extra:,.2f}")
            st.write(
                f"If the selected value increased by {uplift}% over a comparable period, the arithmetic scenario "
                f"would be {base_value + extra:,.2f}, or {extra:,.2f} above the current total. This assumes the "
                "same time window and comparable data; it is not a prediction of what will happen."
            )
        else:
            st.info("The selected field has a negative net total, so this simple uplift scenario is hidden. Check refunds, returns and sign conventions first.")
    else:
        st.info("Select a numeric sales/value field to use the scenario calculator.")

    st.divider()
    st.markdown("### 4. Recommended next actions")
    actions = []
    if product:
        actions.append("Check the leading products' stock, margin and recent trend before increasing promotion.")
    if customer:
        actions.append("Test a small customer-segment campaign and measure incremental purchases against a comparison group.")
    if event:
        actions.append("Investigate products with high views but weak cart/purchase activity, if the event definitions support that comparison.")
    if sales:
        actions.append("Compare the selected value over comparable periods and account for returns, discounts and costs before scaling.")
    if not actions:
        actions.append("Map product, customer, value and date fields to unlock more specific recommendations.")
    for i, action in enumerate(actions, 1):
        st.markdown(f"**{i}.** {action}")
    st.download_button(
        "Download decision notes",
        pd.DataFrame({"Priority": range(1, len(actions) + 1), "Recommended action": actions}).to_csv(index=False).encode("utf-8"),
        "mirror_decision_notes.csv",
        "text/csv"
    )
    st.caption(
        "MIRROR uses the uploaded data only. Recommendations are data-informed prompts for testing, not guarantees. "
        "Reliable profitability or market-size estimates require margin, cost, market and time-period data."
    )

elif page == "Data quality":
    st.subheader("Data quality check")
    missing = df.isna().sum()
    quality = pd.DataFrame({"Column": df.columns.astype(str),
                            "Data type": [str(df[c].dtype) for c in df.columns],
                            "Missing values": [int(missing[c]) for c in df.columns],
                            "Missing (%)": [round(float(missing[c] / max(len(df), 1) * 100), 2) for c in df.columns],
                            "Unique values": [int(df[c].nunique(dropna=True)) for c in df.columns]})
    quality = quality.sort_values("Missing (%)", ascending=False)
    duplicates = int(df.duplicated().sum())
    a, b, c = st.columns(3)
    a.metric("Rows", f"{len(df):,}")
    b.metric("Duplicate rows", f"{duplicates:,}")
    c.metric("Missing cells", f"{int(missing.sum()):,}")
    st.dataframe(quality, use_container_width=True, hide_index=True)
    st.markdown("### Optional cleaning for export")
    remove_dupes = st.checkbox("Remove exact duplicate rows")
    fill_numeric = st.checkbox("Fill missing numeric values with column medians")
    cleaned = df.copy()
    if remove_dupes:
        cleaned = cleaned.drop_duplicates()
    if fill_numeric:
        for col in cleaned.select_dtypes(include=np.number).columns:
            median = cleaned[col].median()
            if pd.notna(median):
                cleaned[col] = cleaned[col].fillna(median)
    st.caption(f"Export contains {len(cleaned):,} rows. Original uploaded data is unchanged.")
    st.download_button("Download cleaned data as CSV", cleaned.to_csv(index=False).encode("utf-8"),
                       "mirror_cleaned_data.csv", "text/csv")
