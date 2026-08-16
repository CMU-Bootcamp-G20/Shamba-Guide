function MainChart({ data }) {

    return (
        <section className="chart-card">


            <div className="bar-chart">

                {data?.map((item) => (

                    <div
                        className="bar-item"
                        key={item.crop}
                    >

                        <div className="bar-label">
                            {item.crop}
                        </div>

                        <div className="bar-container">

                            <div
                                className="bar"
                                style={{
                                    width: `${item.percentage}%`
                                }}
                            />

                        </div>

                        <div className="bar-value">
                            {item.count}
                        </div>

                    </div>

                ))}

            </div>

        </section>
    );
}

export default MainChart;