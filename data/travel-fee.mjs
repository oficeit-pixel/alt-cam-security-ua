// Pure calculation shared by build and browser; no geocoding or guessed distance.
export function settlements(data) {
  return data.areas.flatMap(area=>area.type==='hub'?area.settlements||[]:[area]);
}
export function calculateTravelFee(data,slug) {
  const place=settlements(data).find(area=>area.slug===slug);
  if(!place)return null;
  if(data.fee_rules.free_zones.includes(slug))return 0;
  return distanceFee(data,place.distance_km);
}
export function distanceFee(data,distance) {
  const rate=data.fee_rules.per_km_rate;
  if(typeof distance!=='number'||!Number.isFinite(distance)||distance<0)return null;
  if(typeof rate!=='number'||!Number.isFinite(rate)||rate<0)throw new Error('Invalid travel rate');
  if(data.fee_rules.one_way!==true)throw new Error('Unsupported distance rule');
  return Math.round(distance*rate*100)/100;
}
// Empty locations must never generate doorway pages.
export function canPublishSettlement(place) {
  const translated=value=>value&&['uk','ru'].every(lang=>typeof value[lang]==='string'&&value[lang].trim());
  return typeof place.travel_minutes==='number'&&Number.isFinite(place.travel_minutes)&&place.travel_minutes>0
    && (place.cases||[]).some(c=>c.id&&translated(c.title)&&translated(c.what_done)&&Array.isArray(c.photos)&&c.photos.length>0)
    && (place.faq||[]).filter(f=>translated(f.q)&&translated(f.a)).length>=3;
}
