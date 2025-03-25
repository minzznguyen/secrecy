import { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { FiSave, FiClock, FiChevronDown, FiChevronUp, FiX, FiPlus, FiCheck, FiSlash } from 'react-icons/fi';

const DAYS_OF_WEEK = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday'
];

export function WeeklyAvailability({ onSave }) {
  // Initialize with empty availability for each day
  const [availability, setAvailability] = useState(
    DAYS_OF_WEEK.reduce((acc, day) => {
      acc[day] = []; // Start with empty array instead of default time
      return acc;
    }, {})
  );
  
  // Track which days are available
  const [availableDays, setAvailableDays] = useState(
    DAYS_OF_WEEK.reduce((acc, day) => {
      acc[day] = false; // Start with all days unavailable
      return acc;
    }, {})
  );

  const [saveStatus, setSaveStatus] = useState('');
  const [expanded, setExpanded] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  const addTimeSlot = (day) => {
    // If this is the first time slot, make sure the day is marked as available
    if (!availableDays[day]) {
      setAvailableDays(prev => ({
        ...prev,
        [day]: true
      }));
    }
    
    setAvailability(prev => ({
      ...prev,
      [day]: [...prev[day], { start: '09:00', end: '17:00' }]
    }));
  };

  const removeTimeSlot = (day, index) => {
    setAvailability(prev => {
      const newSlots = prev[day].filter((_, i) => i !== index);
      
      // If removing the last time slot, mark the day as unavailable
      if (newSlots.length === 0) {
        setAvailableDays(prevDays => ({
          ...prevDays,
          [day]: false
        }));
      }
      
      return {
        ...prev,
        [day]: newSlots
      };
    });
  };

  const updateTimeSlot = (day, index, field, value) => {
    setAvailability(prev => ({
      ...prev,
      [day]: prev[day].map((slot, i) => 
        i === index ? { ...slot, [field]: value } : slot
      )
    }));
  };

  const toggleDayAvailability = (day) => {
    setAvailableDays(prev => {
      const newValue = !prev[day];
      
      // If toggling to available and no time slots exist, add one
      if (newValue && availability[day].length === 0) {
        setAvailability(prevAvail => ({
          ...prevAvail,
          [day]: [{ start: '09:00', end: '17:00' }]
        }));
      }
      
      return {
        ...prev,
        [day]: newValue
      };
    });
  };

  const formatAvailabilityForAgent = () => {
    return DAYS_OF_WEEK.map(day => {
      if (!availableDays[day] || availability[day].length === 0) {
        return `${day.substring(0, 3)}: [Unavailable]`;
      }
      
      const daySlots = availability[day]
        .map(slot => `${slot.start}-${slot.end}`)
        .join(', ');
      return `${day.substring(0, 3)}: [${daySlots}]`;
    }).join('; ');
  };

  const handleSave = () => {
    const formattedAvailability = formatAvailabilityForAgent();
    if (onSave) {
      onSave(formattedAvailability);
    }
    setSaveStatus('Availability saved successfully!');
    setIsSaved(true);
    setTimeout(() => {
      setSaveStatus('');
    }, 3000);
  };

  return (
    <Card className="mb-6">
      <CardHeader 
        className={`cursor-pointer ${expanded ? 'pb-2' : 'pb-4'} ${expanded ? 'px-6 pt-6' : 'px-4 pt-4'}`}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg flex items-center">
            <FiClock className="mr-2" />
            Weekly Availability
            {isSaved && <FiCheck className="ml-2 text-green-500" size={16} />}
          </CardTitle>
          <div>
            {expanded ? <FiChevronUp /> : <FiChevronDown />}
          </div>
        </div>
      </CardHeader>
      
      {expanded && (
        <CardContent className="pb-4">
          <div className="space-y-4">
            {DAYS_OF_WEEK.map(day => (
              <div key={day} className="border-b pb-3">
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium">{day}</h3>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => toggleDayAvailability(day)}
                      className={`text-xs px-2 py-1 h-auto ${availableDays[day] ? 'text-green-600' : 'text-red-600'}`}
                    >
                      {availableDays[day] ? (
                        <><FiCheck className="mr-1" size={12} /> Available</>
                      ) : (
                        <><FiSlash className="mr-1" size={12} /> Unavailable</>
                      )}
                    </Button>
                  </div>
                  
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => addTimeSlot(day)}
                    className="flex items-center gap-1"
                  >
                    <FiPlus size={14} />
                    Add Time
                  </Button>
                </div>
                
                {availableDays[day] && availability[day].length > 0 ? (
                  <div className="space-y-2">
                    {availability[day].map((slot, index) => (
                      <div key={index} className="flex items-center gap-2 bg-gray-50 p-2 rounded-md">
                        <div className="flex flex-1 items-center gap-2">
                          <select
                            className="p-2 border rounded text-sm"
                            value={slot.start}
                            onChange={(e) => updateTimeSlot(day, index, 'start', e.target.value)}
                          >
                            {generateTimeOptions().map(time => (
                              <option key={time} value={time}>{time}</option>
                            ))}
                          </select>
                          <span className="text-sm">to</span>
                          <select
                            className="p-2 border rounded text-sm"
                            value={slot.end}
                            onChange={(e) => updateTimeSlot(day, index, 'end', e.target.value)}
                          >
                            {generateTimeOptions().map(time => (
                              <option key={time} value={time}>{time}</option>
                            ))}
                          </select>
                        </div>
                        
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => removeTimeSlot(day, index)}
                          className="text-red-500 hover:text-red-700 p-1 h-auto"
                        >
                          <FiX size={16} />
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-gray-500 italic py-2">
                    {availableDays[day] 
                      ? "Click 'Add Time' to set available hours" 
                      : "Not available on this day"}
                  </div>
                )}
              </div>
            ))}
            
            <Button 
              onClick={handleSave} 
              className="w-full flex items-center justify-center gap-2 mt-2 mb-2"
            >
              <FiSave size={16} />
              Save Availability
            </Button>
            
            {saveStatus && (
              <div className="mt-2 text-center text-green-600 text-sm">
                {saveStatus}
              </div>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}

// Helper function to generate time options in 30-minute increments
function generateTimeOptions() {
  const options = [];
  for (let hour = 0; hour < 24; hour++) {
    for (let minute of ['00', '30']) {
      const formattedHour = hour.toString().padStart(2, '0');
      options.push(`${formattedHour}:${minute}`);
    }
  }
  return options;
} 