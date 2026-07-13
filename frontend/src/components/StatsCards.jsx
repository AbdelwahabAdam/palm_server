const StatsCards = ({ stats }) => {
  if (!stats) return null;

  const cards = [
    { label: 'Total Palms', value: stats.total_palms, color: 'bg-palm-600' },
    { label: 'Total Harvest (kg)', value: stats.total_harvest?.toFixed(1), color: 'bg-blue-600' },
    { label: 'Average Age (years)', value: stats.average_age?.toFixed(1), color: 'bg-amber-600' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {cards.map((card) => (
        <div key={card.label} className={`${card.color} text-white rounded-lg shadow p-6`}>
          <p className="text-sm opacity-90">{card.label}</p>
          <p className="text-3xl font-bold mt-2">{card.value ?? 0}</p>
        </div>
      ))}
    </div>
  );
};

export default StatsCards;
