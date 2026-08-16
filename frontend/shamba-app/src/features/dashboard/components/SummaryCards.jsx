function SummaryCards({ title, value, subtitle, icon }) {
    return (
        <div className="stat-card">

            <div className="stat-card-header">
                <span>{icon}</span>

                <p>{title}</p>
            </div>

            <h2>{value}</h2>

            {subtitle && (
                <span className="stat-subtitle">
                    {subtitle}
                </span>
            )}

        </div>
    );
}

export default SummaryCards;