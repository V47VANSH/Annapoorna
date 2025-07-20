"use client"
import { useParams } from 'next/navigation';

export default function Layout({ children }) {
  const params=useParams();
  const id=params.id;
  return (
    <>
              <nav className="bg-gradient-to-r from-emerald-600 to-lime-500 shadow-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0 flex items-center">
                <svg className="h-8 w-8 text-amber-300" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2L9.1 9.5H2L8 14.5L5.1 22L12 17L18.9 22L16 14.5L22 9.5H14.9L12 2Z" />
                </svg>
                <span className="ml-2 text-white font-bold text-xl font-mono tracking-wider">ANNĀPOORNA</span>
              </div>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-center space-x-8">
                {['Home','Profile', 'Reports', 'Chat'].map((item) => (
                  <a 
                    key={item}
                    href={`/dashboard/${id}/${item.toLowerCase().split(" ")[0]}`}
                    className="text-white hover:text-amber-200 px-3 py-2 rounded-md text-sm font-medium transition-all duration-300 transform hover:scale-105 border-b-2 border-transparent hover:border-amber-300"
                  >
                    {item}
                  </a>
                ))}
              </div>
            </div>
            <button className="md:hidden text-white">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </nav>
        {children}
    </>
  );
}
