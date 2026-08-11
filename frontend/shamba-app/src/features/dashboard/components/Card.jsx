function Card({ title, value, change, description }) {
    const isPositive = change >= 0;

    return (
        <>
        <div className="main-card">
            <p className="main-title">Most Asked Topic{title}</p>

            <h2 className="main-value">{value}</h2>
        </div>
        </>
    );
}

export default Card;