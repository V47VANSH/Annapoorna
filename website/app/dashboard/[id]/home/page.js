'use client'
export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-amber-50 overflow-hidden">
      {/* Navigation Bar */}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Left Column */}
          <div className="relative">
            <div className="absolute -top-12 -left-8 w-72 h-72 bg-emerald-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
            <div className="absolute top-0 right-10 w-72 h-72 bg-amber-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
            <div className="absolute -bottom-8 left-20 w-72 h-72 bg-lime-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000"></div>
            
            <div className="relative space-y-8">
              <h1 className="text-5xl font-extrabold tracking-tight text-gray-900 sm:text-6xl">
                <span className="block bg-clip-text text-transparent bg-gradient-to-r from-emerald-600 to-amber-600">
                  Farm Smarter,
                </span>
                <span className="block mt-2 bg-clip-text text-transparent bg-gradient-to-r from-lime-600 to-emerald-600">
                  Grow Better
                </span>
              </h1>
              <p className="text-xl text-gray-700 max-w-lg">
                Meet Annāpoorna - your AI-powered agricultural assistant. 
                Get real-time insights, expert advice, and smart solutions 
                for your farming needs.
              </p>
              <div className="bg-white rounded-2xl shadow-xl p-6 border-4 border-lime-200 transform rotate-1">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <div className="bg-emerald-100 p-2 rounded-full">
                      <svg className="h-8 w-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-medium text-gray-900">Annāpoorna says:</h3>
                    <div className="mt-2 text-gray-700">
                      <p>Hello how are you</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="flex justify-center">
            <div className="relative">
              <div className="bg-gradient-to-br from-lime-100 to-amber-100 border-8 border-white rounded-[40px] shadow-2xl w-full max-w-md h-[500px] overflow-hidden relative transform rotate-3">
                {/* Decorative Elements */}
                <div className="absolute top-10 left-10 w-24 h-24 rounded-full bg-gradient-to-r from-amber-300 to-amber-200 opacity-60 blur-md"></div>
                <div className="absolute bottom-16 right-12 w-32 h-32 rounded-full bg-gradient-to-r from-emerald-300 to-emerald-200 opacity-40 blur-lg"></div>
                
                {/* Chat Container */}
                <div className="absolute inset-0 flex flex-col p-6">
                  <div className="text-center py-4">
                    <h2 className="text-xl font-bold text-emerald-800">Annāpoorna Chat</h2>
                    <div className="mt-1 h-1 w-20 bg-gradient-to-r from-emerald-500 to-lime-500 rounded-full mx-auto"></div>
                  </div>
                  
                  <div className="flex-grow overflow-y-auto space-y-4 py-4">
                    <div className="flex justify-start">
                      <div className="bg-white rounded-2xl rounded-tl-none px-5 py-3 max-w-xs shadow-md border border-emerald-100">
                        <p className="text-gray-700">Hello! I'm Annāpoorna, your farming assistant. How can I help today?</p>
                      </div>
                    </div>
                    <div className="flex justify-end">
                      <div className="bg-gradient-to-r from-emerald-500 to-lime-500 rounded-2xl rounded-tr-none px-5 py-3 max-w-xs shadow-md">
                        <p className="text-white">Hello how are you</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-auto">
                    <div className="flex items-center">
                      <input
                        type="text"
                        placeholder="Ask about crops, weather, or soil..."
                        className="flex-grow bg-white rounded-l-full py-4 px-6 text-gray-700 focus:outline-none focus:ring-2 focus:ring-emerald-300 border-t border-l border-b border-emerald-200"
                      />
                      <button className="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white rounded-r-full px-6 py-4 font-bold transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-amber-300">
                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Decorative Plants */}
              <div className="absolute -bottom-6 -left-6">
                <svg className="h-24 w-24 text-lime-400" viewBox="0 0 100 100">
                  <path fill="currentColor" d="M50,10 C60,0 80,15 70,35 C85,30 90,50 70,60 C85,65 75,85 60,80 C65,95 40,95 45,80 C30,85 15,70 30,60 C10,55 20,35 35,40 C25,20 45,15 50,10 Z" />
                </svg>
              </div>
              <div className="absolute -top-8 -right-8 rotate-12">
                <svg className="h-20 w-20 text-emerald-500" viewBox="0 0 100 100">
                  <path fill="currentColor" d="M30,10 C40,0 60,20 50,40 C65,35 80,50 65,65 C80,60 70,80 55,75 C65,95 35,95 45,75 C25,80 15,60 30,50 C10,45 25,25 40,30 C30,15 35,5 30,10 Z" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Animated Blobs */}
      <style jsx>{`
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
}