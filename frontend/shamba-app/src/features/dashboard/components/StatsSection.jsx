import SummaryCards from "./SummaryCards";

function StatsSection({ analytics }) {

    return (
        <section className="dashboard-stats">

            <SummaryCards
                title="Total Messages"
                value={analytics?.total_messages || 0}
                subtitle="Messages received"
            />

            <SummaryCards
                title="Conversations"
                value={analytics?.total_conversations || 0}
                subtitle="Chat sessions"
            />

            <SummaryCards
                title="Top Crop"
                value={analytics?.top_crop || "N/A"}
                subtitle="Most discussed crop"
            />

        </section>
    );
}

export default StatsSection;